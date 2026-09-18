use ghvirtualgamepad::{Mapper, Profile};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    io::{self, BufRead, Write},
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};

#[cfg(target_os = "linux")]
mod linux;
#[cfg(target_os = "linux")]
use linux::Backend;
#[cfg(target_os = "windows")]
mod windows;
#[cfg(target_os = "windows")]
use windows::Backend;

#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
enum Command {
    Scan,
    Select {
        player: usize,
        device: String,
    },
    Profile {
        player: usize,
        profile: Profile,
    },
    Start,
    Stop,
    Inject {
        player: usize,
        source: String,
        kind: u16,
        code: u16,
        value: i32,
    },
    Quit,
}

fn send(value: Value) {
    let mut out = io::stdout().lock();
    if writeln!(out, "{value}").and_then(|_| out.flush()).is_err() {
        panic!("Parent connection closed");
    }
}

fn main() {
    let demo = std::env::args().any(|a| a == "--demo");
    #[cfg(target_os = "windows")]
    if std::env::args().any(|a| a == "--probe-gamepads") {
        if let Err(message) = windows::probe() {
            send(json!({"type":"error","message":message}));
            std::process::exit(1);
        }
        return;
    }
    #[cfg(not(any(target_os = "linux", target_os = "windows")))]
    if !demo {
        send(
            json!({"type":"error","message":"Native controllers require Linux or Windows. Use --demo on this platform."}),
        );
        return;
    }
    let (tx, rx) = mpsc::sync_channel(256);
    thread::spawn(move || {
        for line in io::stdin().lock().lines() {
            match line {
                Ok(line) if line.len() <= 65536 => {
                    if tx
                        .send(serde_json::from_str::<Command>(&line).map_err(|e| e.to_string()))
                        .is_err()
                    {
                        return;
                    }
                }
                _ => break,
            }
        }
        let _ = tx.send(Ok(Command::Quit));
    });
    let mut maps = [Mapper::default(), Mapper::default()];
    let mut selected = [String::new(), String::new()];
    let mut running = false;
    #[cfg(any(target_os = "linux", target_os = "windows"))]
    let mut backend = Backend::default();
    send(json!({"type":"hello","protocol":1,"demo":demo}));
    let mut last = Instant::now();
    let mut publish = Instant::now();
    let mut scan = Instant::now() - Duration::from_secs(3);
    'engine: loop {
        for _ in 0..64 {
            let Ok(command) = rx.try_recv() else {
                break;
            };
            if matches!(&command, Ok(Command::Quit)) {
                break 'engine;
            }
            let result: Result<(), String> = (|| {
                let command = command?;
                match command {
                    Command::Quit => unreachable!(),
                    Command::Scan => scan = Instant::now() - Duration::from_secs(3),
                    Command::Stop => {
                        running = false;
                        #[cfg(any(target_os = "linux", target_os = "windows"))]
                        backend.stop();
                        for m in &mut maps {
                            m.reset();
                        }
                    }
                    Command::Select { player, device } => {
                        if player > 1 || running {
                            return Err("Stop controllers before changing devices".into());
                        }
                        if !device.is_empty() && selected[1 - player] == device {
                            return Err("Device is already assigned to the other player".into());
                        }
                        #[cfg(any(target_os = "linux", target_os = "windows"))]
                        if !demo {
                            backend.select(player, &device)?;
                        }
                        if demo
                            && !device.is_empty()
                            && !["demo-1", "demo-2"].contains(&device.as_str())
                        {
                            return Err("Unknown demo device".into());
                        }
                        selected[player] = device;
                        maps[player].reset();
                    }
                    Command::Profile { player, profile } => {
                        if player > 1 || running {
                            return Err("Stop controllers before editing mappings".into());
                        }
                        profile.validate()?;
                        maps[player].profile = profile;
                        maps[player].reset();
                    }
                    Command::Start => {
                        if running {
                            return Ok(());
                        }
                        if selected.iter().all(|s| s.is_empty()) {
                            return Err("Select at least one device".into());
                        }
                        for p in 0..2 {
                            if !selected[p].is_empty() && maps[p].profile.bindings.is_empty() {
                                return Err(format!("Player {} has no bindings", p + 1));
                            }
                        }
                        #[cfg(any(target_os = "linux", target_os = "windows"))]
                        if !demo {
                            backend.start(&maps)?;
                        }
                        for m in &mut maps {
                            m.reset();
                        }
                        running = true;
                    }
                    Command::Inject {
                        player,
                        source,
                        kind,
                        code,
                        value,
                    } => {
                        if !demo || player > 1 || selected[player].is_empty() {
                            return Err(
                                "Injection is only available for a selected demo device".into()
                            );
                        }
                        maps[player].input(&source, kind, code, value);
                        send(
                            json!({"type":"input","player":player,"source":source,"kind":kind,"code":code,"value":value,"min":0,"max":255}),
                        );
                    }
                }
                Ok(())
            })();
            if let Err(message) = result {
                send(json!({"type":"error","message":message}));
            }
            send(json!({"type":"status","running":running,"selected":selected}));
        }
        let now = Instant::now();
        let elapsed = now.duration_since(last).as_secs_f64().min(0.1);
        last = now;
        #[cfg(any(target_os = "linux", target_os = "windows"))]
        if !demo {
            backend.poll(&mut maps);
        }
        for m in &mut maps {
            m.tick(elapsed);
        }
        #[cfg(any(target_os = "linux", target_os = "windows"))]
        if running && !demo {
            if let Err(e) = backend.emit(&maps) {
                backend.stop();
                running = false;
                for m in &mut maps {
                    m.reset();
                }
                send(json!({"type":"error","message":e}));
                send(json!({"type":"status","running":false,"selected":selected}));
            }
        }
        if scan.elapsed() >= Duration::from_secs(2) {
            scan = now;
            if demo {
                send(
                    json!({"type":"devices","devices":[{"id":"demo-1","label":"Simulated keyboard A · USB port 1","sources":["keyboard"]},{"id":"demo-2","label":"Simulated keyboard B · USB port 2","sources":["keyboard"]}]}),
                );
            }
            #[cfg(any(target_os = "linux", target_os = "windows"))]
            if !demo {
                backend.refresh();
                send(json!({"type":"devices","devices":backend.list()}));
            }
        }
        if publish.elapsed() >= Duration::from_millis(33) {
            publish = now;
            send(json!({"type":"state","players":[maps[0].state,maps[1].state]}));
        }
        thread::sleep(Duration::from_millis(4));
    }
}
