//! Windows keyboard capture through the official Interception client DLL.
//! Only explicitly selected keyboard slots are filtered; unselected input is untouched.
use ghvirtualgamepad::Mapper;
use libloading::Library;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    ffi::c_void,
    path::PathBuf,
    rc::Rc,
    sync::atomic::{AtomicU32, Ordering},
};
use vigem_client::{Client, TargetId, XButtons, XGamepad, Xbox360Wired};

static SELECTED: AtomicU32 = AtomicU32::new(0);
unsafe extern "C" fn selected(device: i32) -> i32 {
    i32::from((1..=10).contains(&device) && SELECTED.load(Ordering::Relaxed) & (1 << device) != 0)
}
unsafe extern "C" fn keyboards(device: i32) -> i32 {
    i32::from((1..=10).contains(&device))
}

#[repr(C)]
#[derive(Default, Copy, Clone)]
struct Stroke {
    code: u16,
    state: u16,
    information: u32,
}
type Context = *mut c_void;
type Create = unsafe extern "C" fn() -> Context;
type Destroy = unsafe extern "C" fn(Context);
type Filter = unsafe extern "C" fn(Context, unsafe extern "C" fn(i32) -> i32, u16);
type Wait = unsafe extern "C" fn(Context, u32) -> i32;
type Receive = unsafe extern "C" fn(Context, i32, *mut Stroke, u32) -> i32;
type Send = unsafe extern "C" fn(Context, i32, *const Stroke, u32) -> i32;
type Hardware = unsafe extern "C" fn(Context, i32, *mut c_void, u32) -> u32;

struct Input {
    context: Context,
    destroy: Destroy,
    filter: Filter,
    wait: Wait,
    receive: Receive,
    send: Send,
    hardware: Hardware,
    _library: Library,
}
impl Input {
    fn open() -> Result<Self, String> {
        let path = std::env::var_os("GHVP_INTERCEPTION_DLL")
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                std::env::current_exe()
                    .unwrap()
                    .parent()
                    .unwrap()
                    .join("drivers/interception.dll")
            });
        if !path.is_absolute() {
            return Err("Interception DLL path must be absolute".into());
        }
        // The fixed, application-owned path avoids DLL search through the working directory.
        unsafe {
            let library = Library::new(&path).map_err(|_| {
                "Interception client is missing. Run the Windows dependency setup.".to_string()
            })?;
            let create: Create = *library
                .get(b"interception_create_context\0")
                .map_err(|e| e.to_string())?;
            let destroy = *library
                .get(b"interception_destroy_context\0")
                .map_err(|e| e.to_string())?;
            let filter = *library
                .get(b"interception_set_filter\0")
                .map_err(|e| e.to_string())?;
            let wait = *library
                .get(b"interception_wait_with_timeout\0")
                .map_err(|e| e.to_string())?;
            let receive = *library
                .get(b"interception_receive\0")
                .map_err(|e| e.to_string())?;
            let send = *library
                .get(b"interception_send\0")
                .map_err(|e| e.to_string())?;
            let hardware = *library
                .get(b"interception_get_hardware_id\0")
                .map_err(|e| e.to_string())?;
            let context = create();
            if context.is_null() {
                return Err(
                    "Cannot open Interception. Install its drivers and restart Windows.".into(),
                );
            }
            Ok(Self {
                context,
                destroy,
                filter,
                wait,
                receive,
                send,
                hardware,
                _library: library,
            })
        }
    }
    fn id(&self, slot: i32) -> String {
        let mut buffer = [0u16; 1024];
        let bytes = unsafe { (self.hardware)(self.context, slot, buffer.as_mut_ptr().cast(), 2048) }
            as usize;
        if bytes == 0 || bytes > 2048 {
            return String::new();
        }
        String::from_utf16_lossy(&buffer[..bytes / 2])
            .trim_end_matches('\0')
            .to_string()
    }
    fn filters(&self, mask: u32) {
        unsafe {
            (self.filter)(self.context, keyboards, 0);
        }
        SELECTED.store(mask, Ordering::Relaxed);
        unsafe {
            (self.filter)(self.context, selected, 0xffff);
        }
    }
}
impl Drop for Input {
    fn drop(&mut self) {
        unsafe {
            (self.destroy)(self.context);
        }
    }
}

#[derive(Default)]
struct Slot {
    id: String,
    number: i32,
    output: Option<Xbox360Wired<Rc<Client>>>,
}
#[derive(Default)]
pub struct Backend {
    input: Option<Input>,
    devices: BTreeMap<String, i32>,
    slots: [Slot; 2],
    announced_error: bool,
    capturing: bool,
}

impl Backend {
    pub fn refresh(&mut self) {
        if self.input.is_none() {
            match Input::open() {
                Ok(input) => {
                    self.input = Some(input);
                    self.announced_error = false;
                }
                Err(message) => {
                    if !self.announced_error {
                        super::send(json!({"type":"error","message":message}));
                        self.announced_error = true;
                    }
                    return;
                }
            }
        }
        self.devices.clear();
        let input = self.input.as_ref().unwrap();
        for slot in 1..=10 {
            let hardware = input.id(slot);
            if !hardware.is_empty() {
                self.devices.insert(format!("win:{slot}:{hardware}"), slot);
            }
        }
    }
    pub fn list(&self) -> Vec<Value> {
        self.devices.iter().map(|(id, slot)| json!({"id":id,"label":format!("Keyboard slot {slot} · {}",id.splitn(3, ':').nth(2).unwrap_or("")),"sources":["keyboard"]})).collect()
    }
    pub fn select(&mut self, player: usize, id: &str) -> Result<(), String> {
        self.refresh();
        let number = if id.is_empty() {
            0
        } else {
            *self
                .devices
                .get(id)
                .ok_or("Keyboard is unavailable. Install Interception and restart Windows.")?
        };
        self.slots[player] = Slot {
            id: id.into(),
            number,
            output: None,
        };
        let mask = self
            .slots
            .iter()
            .filter(|s| s.number != 0)
            .fold(0, |mask, s| mask | (1 << s.number));
        if let Some(input) = &self.input {
            input.filters(mask);
        }
        Ok(())
    }
    pub fn start(&mut self, maps: &[Mapper; 2]) -> Result<(), String> {
        self.refresh();
        let client = Rc::new(Client::connect().map_err(|e| {
            format!("ViGEmBus unavailable: {e}. Install its driver and restart Windows.")
        })?);
        let result = (|| {
            for (p, slot) in self.slots.iter_mut().enumerate() {
                if slot.number == 0 {
                    if !slot.id.is_empty() {
                        return Err("A selected keyboard disconnected. Select it again.".into());
                    }
                    continue;
                }
                if !self.devices.contains_key(&slot.id) {
                    return Err("A selected keyboard disconnected. Select it again.".into());
                }
                if maps[p]
                    .profile
                    .bindings
                    .values()
                    .any(|b| b.source != "keyboard" || b.kind != 1)
                {
                    return Err("Windows requires keyboard bindings taught on Windows".into());
                }
                let mut output = Xbox360Wired::new(client.clone(), TargetId::XBOX360_WIRED);
                output.plugin().map_err(|e| e.to_string())?;
                output.wait_ready().map_err(|e| e.to_string())?;
                initialize(&mut output, &XGamepad::default())?;
                slot.output = Some(output);
            }
            self.capturing = true;
            Ok(())
        })();
        if result.is_err() {
            self.stop();
        }
        result
    }
    pub fn stop(&mut self) {
        self.capturing = false;
        for slot in &mut self.slots {
            slot.output = None;
        }
    }
    pub fn poll(&mut self, maps: &mut [Mapper; 2]) {
        let Some(input) = &self.input else {
            return;
        };
        for (p, slot) in self.slots.iter_mut().enumerate() {
            if slot.number != 0 && !self.devices.contains_key(&slot.id) {
                maps[p].reset();
                slot.output = None;
                slot.number = 0;
                super::send(json!({"type":"connection","player":p,"connected":false}));
            }
        }
        for _ in 0..128 {
            let device = unsafe { (input.wait)(input.context, 0) };
            if device == 0 {
                break;
            }
            let mut stroke = Stroke::default();
            if unsafe { (input.receive)(input.context, device, &mut stroke, 1) } != 1 {
                break;
            }
            let player = self.slots.iter().position(|s| s.number == device);
            if !self.capturing || player.is_none() {
                unsafe {
                    (input.send)(input.context, device, &stroke, 1);
                }
            }
            if let Some(p) = player {
                let code = stroke.code | ((stroke.state & 6) << 8);
                let value = i32::from(stroke.state & 1 == 0);
                maps[p].input("keyboard", 1, code, value);
                super::send(
                    json!({"type":"input","player":p,"source":"keyboard","kind":1,"code":code,"value":value,"min":0,"max":1}),
                );
            }
        }
    }
    pub fn emit(&mut self, maps: &[Mapper; 2]) -> Result<(), String> {
        for (p, slot) in self.slots.iter_mut().enumerate() {
            if let Some(output) = &mut slot.output {
                output
                    .update(&report(&maps[p]))
                    .map_err(|e| e.to_string())?;
            }
        }
        Ok(())
    }
}
impl Drop for Backend {
    fn drop(&mut self) {
        self.stop();
        self.input = None;
    }
}

fn report(map: &Mapper) -> XGamepad {
    let mut buttons = 0u16;
    for (action, flag) in [
        ("green", XButtons::A),
        ("red", XButtons::B),
        ("yellow", XButtons::Y),
        ("blue", XButtons::X),
        ("orange", XButtons::LB),
        ("extra", XButtons::RB),
        ("start", XButtons::START),
        ("select", XButtons::BACK),
    ] {
        if map.pressed(action) && (action != "extra" || !map.profile.ghwtde_extra_fix) {
            buttons |= flag;
        }
    }
    let (x, y) = map.hat();
    if x < 0 {
        buttons |= XButtons::LEFT;
    }
    if x > 0 {
        buttons |= XButtons::RIGHT;
    }
    if y < 0 {
        buttons |= XButtons::UP;
    }
    if y > 0 {
        buttons |= XButtons::DOWN;
    }
    XGamepad {
        buttons: XButtons(buttons),
        thumb_ry: (map.state.whammy * 32767.0).round() as i16,
        ..XGamepad::default()
    }
}

fn initialize(pad: &mut Xbox360Wired<Rc<Client>>, state: &XGamepad) -> Result<(), String> {
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
    loop {
        match pad.update(state) {
            Ok(()) => return Ok(()),
            Err(e) if std::time::Instant::now() >= deadline => {
                return Err(format!("Controller did not become ready: {e}"));
            }
            Err(_) => std::thread::sleep(std::time::Duration::from_millis(50)),
        }
    }
}

pub fn probe() -> Result<(), String> {
    #[repr(C)]
    #[derive(Default)]
    struct State {
        packet: u32,
        gamepad: XGamepad,
    }
    type GetState = unsafe extern "system" fn(u32, *mut State) -> u32;
    let system = std::env::var_os("SystemRoot").ok_or("SystemRoot is missing")?;
    let library = unsafe { Library::new(PathBuf::from(system).join("System32/xinput1_4.dll")) }
        .map_err(|e| e.to_string())?;
    let get: GetState = unsafe {
        *library
            .get(b"XInputGetState\0")
            .map_err(|e| e.to_string())?
    };
    let client = Rc::new(Client::connect().map_err(|e| format!("connect: {e}"))?);
    let mut pads = Vec::new();
    for player in 0..2 {
        let mut pad = Xbox360Wired::new(client.clone(), TargetId::XBOX360_WIRED);
        pad.plugin().map_err(|e| format!("plugin: {e}"))?;
        pad.wait_ready().map_err(|e| format!("wait_ready: {e}"))?;
        initialize(
            &mut pad,
            &XGamepad {
                thumb_lx: 12345 + player,
                ..XGamepad::default()
            },
        )?;
        pads.push(pad);
    }
    // Bus user indices can be stale during enumeration. Verify the actual XInput reports.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    loop {
        let mut found = [None; 2];
        for index in 0..4 {
            let mut state = State::default();
            if unsafe { get(index, &mut state) } == 0 {
                for (player, slot) in found.iter_mut().enumerate() {
                    if state.gamepad.thumb_lx == 12345 + player as i16 {
                        *slot = Some(index);
                    }
                }
            }
        }
        if found.iter().all(Option::is_some) && found[0] != found[1] {
            super::send(json!({"type":"probe","verified":true,"xinput_slots":found}));
            return Ok(());
        }
        if std::time::Instant::now() >= deadline {
            return Err(format!("Two independent XInput reports were not found: {found:?}. Free two controller slots."));
        }
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn output_layout_and_axis() {
        let mut map = Mapper::default();
        map.state.buttons.insert("green".into(), true);
        map.state.buttons.insert("extra".into(), true);
        map.state.buttons.insert("strum_down".into(), true);
        map.state.whammy = 1.0;
        let output = report(&map);
        assert_eq!(
            output.buttons.raw,
            XButtons::A | XButtons::RB | XButtons::DOWN
        );
        assert_eq!(output.thumb_ry, 32767);
    }

    #[test]
    fn ghwtde_fix_outputs_extra_as_dpad_left_only() {
        let mut map = Mapper::default();
        map.profile.ghwtde_extra_fix = true;
        map.state.buttons.insert("extra".into(), true);
        let output = report(&map);
        assert_eq!(output.buttons.raw, XButtons::LEFT);
    }
}
