use evdev::{
    uinput::VirtualDevice, AbsInfo, AbsoluteAxisCode, AttributeSet, BusType, Device, InputEvent,
    InputId, KeyCode, UinputAbsSetup,
};
use ghvirtualgamepad::Mapper;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs, io,
    path::PathBuf,
    time::{Duration, Instant},
};

struct Node {
    source: String,
    path: PathBuf,
    sysfs: PathBuf,
}
struct Group {
    label: String,
    nodes: Vec<Node>,
}
struct Reader {
    source: String,
    device: Device,
    axes: BTreeMap<u16, (i32, i32)>,
}
struct Slot {
    id: String,
    readers: Vec<Reader>,
    output: Option<VirtualDevice>,
    retry: Instant,
    last_output: Vec<(u16, u16, i32)>,
}
impl Default for Slot {
    fn default() -> Self {
        Self {
            id: String::new(),
            readers: vec![],
            output: None,
            retry: Instant::now(),
            last_output: vec![],
        }
    }
}
#[derive(Default)]
pub struct Backend {
    groups: BTreeMap<String, Group>,
    slots: [Slot; 2],
}

fn text(path: PathBuf) -> String {
    fs::read_to_string(path)
        .unwrap_or_default()
        .trim()
        .to_string()
}

impl Backend {
    pub fn refresh(&mut self) {
        let mut groups: BTreeMap<String, Group> = BTreeMap::new();
        let Ok(entries) = fs::read_dir("/sys/class/input") else {
            return;
        };
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().into_owned();
            if !name.starts_with("event") {
                continue;
            }
            let Ok(sys) = fs::canonicalize(entry.path().join("device")) else {
                continue;
            };
            // Only physical USB devices are eligible. Virtual output can never feed itself.
            let Some(usb) = sys
                .ancestors()
                .find(|p| p.join("idVendor").exists())
                .map(|p| p.to_path_buf())
            else {
                continue;
            };
            let vendor = text(usb.join("idVendor"));
            let product = text(usb.join("idProduct"));
            let serial = text(usb.join("serial"));
            let port = usb.file_name().unwrap_or_default().to_string_lossy();
            // Port remains part of identity even with serials: duplicate serials exist in inexpensive receivers.
            let id = format!("{vendor}:{product}:{serial}@{port}");
            let interface = sys
                .ancestors()
                .find_map(|p| {
                    let value = text(p.join("bInterfaceNumber"));
                    if value.is_empty() {
                        None
                    } else {
                        Some(value)
                    }
                })
                .unwrap_or_else(|| "00".into());
            let physical = text(sys.join("phys"));
            let suffix = physical.rsplit('/').next().unwrap_or("input0");
            let source = format!("if{interface}/{suffix}/{}", text(sys.join("name")));
            let label = format!(
                "{} · {vendor}:{product} · USB {port}",
                text(sys.join("name"))
            );
            groups
                .entry(id)
                .or_insert_with(|| Group {
                    label,
                    nodes: vec![],
                })
                .nodes
                .push(Node {
                    source,
                    path: PathBuf::from("/dev/input").join(name),
                    sysfs: sys,
                });
        }
        for g in groups.values_mut() {
            g.nodes.sort_by(|a, b| a.source.cmp(&b.source));
        }
        self.groups = groups;
    }
    pub fn list(&self) -> Vec<Value> {
        self.groups.iter().map(|(id, g)| json!({"id":id,"label":g.label,"sources":g.nodes.iter().map(|n| &n.source).collect::<Vec<_>>()})).collect()
    }
    fn open(group: &Group, grab: bool) -> Result<Vec<Reader>, String> {
        let mut readers = Vec::new();
        for node in &group.nodes {
            let current = fs::canonicalize(
                PathBuf::from("/sys/class/input")
                    .join(node.path.file_name().ok_or("Invalid event node")?)
                    .join("device"),
            )
            .map_err(|_| "Device changed during selection; rescan")?;
            if current != node.sysfs {
                return Err("Device node was reused; rescan before selecting it".into());
            }
            if readers.iter().any(|r: &Reader| r.source == node.source) {
                return Err(
                    "Receiver exposes ambiguous interfaces; device diagnostics are required".into(),
                );
            }
            let mut device = Device::open(&node.path).map_err(|e| {
                format!(
                    "{}: {e}. Configure device permissions first.",
                    node.path.display()
                )
            })?;
            device.set_nonblocking(true).map_err(|e| e.to_string())?;
            if grab {
                device.grab().map_err(|e| {
                    format!("Cannot exclusively capture {}: {e}", node.path.display())
                })?;
            }
            let axes = device
                .get_abs_state()
                .map(|axes| {
                    axes.iter()
                        .enumerate()
                        .map(|(i, a)| (i as u16, (a.minimum, a.maximum)))
                        .collect()
                })
                .unwrap_or_default();
            readers.push(Reader {
                source: node.source.clone(),
                device,
                axes,
            });
        }
        Ok(readers)
    }
    pub fn select(&mut self, player: usize, id: &str) -> Result<(), String> {
        self.refresh();
        let readers = if id.is_empty() {
            vec![]
        } else {
            Self::open(
                self.groups.get(id).ok_or("Device is no longer connected")?,
                false,
            )?
        };
        self.slots[player] = Slot {
            id: id.into(),
            readers,
            ..Slot::default()
        };
        Ok(())
    }
    pub fn start(&mut self, maps: &[Mapper; 2]) -> Result<(), String> {
        // Build all outputs and grabs transactionally. Any failure releases everything.
        let result = (|| {
            for (p, map) in maps.iter().enumerate() {
                let slot = &mut self.slots[p];
                if slot.id.is_empty() {
                    continue;
                }
                if slot.readers.is_empty() {
                    return Err("A selected device is disconnected".into());
                }
                for binding in map.profile.bindings.values() {
                    if !slot.readers.iter().any(|r| r.source == binding.source) {
                        return Err(format!(
                            "Player {}: a binding belongs to another receiver interface; remap it",
                            p + 1
                        ));
                    }
                }
                for reader in &mut slot.readers {
                    while let Ok(events) = reader.device.fetch_events() {
                        if events.count() == 0 {
                            break;
                        }
                    }
                    reader.device.grab().map_err(|e| e.to_string())?;
                }
                slot.output = Some(create_pad(p).map_err(|e| {
                    format!("Cannot create gamepad: {e}. Check /dev/uinput permissions.")
                })?);
                slot.last_output.clear();
            }
            Ok(())
        })();
        if result.is_err() {
            self.stop();
        }
        result
    }
    pub fn stop(&mut self) {
        for slot in &mut self.slots {
            slot.output = None;
            slot.last_output.clear();
            // Closing descriptors guarantees release even if an ungrab ioctl would fail.
            slot.readers.clear();
            slot.retry = Instant::now() - Duration::from_secs(3);
        }
    }
    pub fn poll(&mut self, maps: &mut [Mapper; 2]) {
        for (p, slot) in self.slots.iter_mut().enumerate() {
            if slot.id.is_empty() {
                continue;
            }
            if slot.readers.is_empty() && slot.retry.elapsed() > Duration::from_secs(2) {
                slot.retry = Instant::now();
                if let Some(group) = self.groups.get(&slot.id) {
                    if let Ok(readers) = Self::open(group, slot.output.is_some()) {
                        slot.readers = readers;
                        super::send(json!({"type":"connection","player":p,"connected":true}));
                    }
                }
            }
            let mut lost = false;
            for reader in &mut slot.readers {
                // Bound work per tick so a noisy device cannot starve stop/quit commands.
                match reader.device.fetch_events() {
                    Ok(events) => {
                        for e in events {
                            let kind = e.event_type().0;
                            if kind != 1 && kind != 3 {
                                continue;
                            }
                            maps[p].input(&reader.source, kind, e.code(), e.value());
                            let (min, max) = reader.axes.get(&e.code()).copied().unwrap_or((0, 1));
                            super::send(
                                json!({"type":"input","player":p,"source":reader.source,"kind":kind,"code":e.code(),"value":e.value(),"min":min,"max":max}),
                            );
                        }
                    }
                    Err(e) if e.kind() == io::ErrorKind::WouldBlock => (),
                    Err(_) => {
                        lost = true;
                        break;
                    }
                }
            }
            if lost {
                slot.readers.clear();
                maps[p].reset();
                slot.retry = Instant::now();
                // Preserve the virtual device and player slot through receiver reconnection.
                super::send(json!({"type":"connection","player":p,"connected":false}));
            }
        }
    }
    pub fn emit(&mut self, maps: &[Mapper; 2]) -> Result<(), String> {
        for (p, slot) in self.slots.iter_mut().enumerate() {
            let Some(output) = &mut slot.output else {
                continue;
            };
            let map = &maps[p];
            let mut state: Vec<(u16, u16, i32)> = [
                ("green", 304),
                ("red", 305),
                ("blue", 307),
                ("yellow", 308),
                ("orange", 310),
                ("extra", 311),
                ("select", 314),
                ("start", 315),
            ]
            .iter()
            .map(|(action, code)| {
                let pressed =
                    map.pressed(action) && (*action != "extra" || !map.profile.ghwtde_extra_fix);
                (1, *code, pressed as i32)
            })
            .collect();
            let (x, y) = map.hat();
            state.extend([
                (3, 16, x),
                (3, 17, y),
                (3, 0, 0),
                (3, 1, 0),
                (3, 2, 0),
                (3, 3, 0),
                (3, 4, (map.state.whammy * 32767.0).round() as i32),
                (3, 5, 0),
            ]);
            if state != slot.last_output {
                let events: Vec<_> = state
                    .iter()
                    .map(|(kind, code, value)| InputEvent::new(*kind, *code, *value))
                    .collect();
                output.emit(&events).map_err(|e| e.to_string())?;
                slot.last_output = state;
            }
        }
        Ok(())
    }
}

fn create_pad(player: usize) -> io::Result<VirtualDevice> {
    let name = format!("GHVirtualGamePad Player {}", player + 1);
    let mut keys = AttributeSet::<KeyCode>::new();
    for code in [304, 305, 307, 308, 310, 311, 314, 315, 316, 317, 318] {
        keys.insert(KeyCode(code));
    }
    let mut builder = VirtualDevice::builder()?
        .name(&name)
        .input_id(InputId::new(BusType::BUS_USB, 0x045e, 0x028e, 0x0114))
        .with_keys(&keys)?;
    for code in [0, 1, 2, 3, 4, 5, 16, 17] {
        let (min, max) = if code >= 16 {
            (-1, 1)
        } else if code == 2 || code == 5 {
            (0, 255)
        } else {
            (-32768, 32767)
        };
        builder = builder.with_absolute_axis(&UinputAbsSetup::new(
            AbsoluteAxisCode(code),
            AbsInfo::new(0, min, max, 0, 0, 0),
        ))?;
    }
    builder.build()
}
