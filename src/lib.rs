use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const ACTIONS: [&str; 15] = [
    "green",
    "red",
    "yellow",
    "blue",
    "orange",
    "strum_up",
    "strum_down",
    "start",
    "select",
    "up",
    "down",
    "left",
    "right",
    "extra",
    "whammy",
];

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Binding {
    pub source: String,
    pub kind: u16,
    pub code: u16,
    pub rest: i32,
    pub full: i32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Profile {
    pub bindings: BTreeMap<String, Binding>,
    pub rise_ms: f64,
    pub return_ms: f64,
    #[serde(default)]
    pub ghwtde_extra_fix: bool,
}

impl Default for Profile {
    fn default() -> Self {
        Self {
            bindings: BTreeMap::new(),
            rise_ms: 250.0,
            return_ms: 180.0,
            ghwtde_extra_fix: false,
        }
    }
}

impl Profile {
    pub fn validate(&self) -> Result<(), String> {
        if !self.rise_ms.is_finite()
            || !self.return_ms.is_finite()
            || !(10.0..=10000.0).contains(&self.rise_ms)
            || !(10.0..=10000.0).contains(&self.return_ms)
        {
            return Err("Whammy speed must be between 10 and 10000 ms".into());
        }
        for (action, binding) in &self.bindings {
            if !ACTIONS.contains(&action.as_str())
                || ![1, 3].contains(&binding.kind)
                || (binding.kind == 3 && binding.rest == binding.full)
            {
                return Err(format!("Invalid binding: {action}"));
            }
        }
        Ok(())
    }
}

#[derive(Default, Clone, Debug, PartialEq, Serialize)]
pub struct PadState {
    pub buttons: BTreeMap<String, bool>,
    pub whammy: f64,
}

#[derive(Default)]
pub struct Mapper {
    pub profile: Profile,
    pub state: PadState,
    whammy_pressed: bool,
}

impl Mapper {
    pub fn reset(&mut self) {
        self.state = PadState::default();
        self.whammy_pressed = false;
    }

    pub fn input(&mut self, source: &str, kind: u16, code: u16, value: i32) {
        if kind == 1 && value == 2 {
            return;
        }
        for (action, binding) in &self.profile.bindings {
            if binding.source != source || binding.kind != kind || binding.code != code {
                continue;
            }
            let amount = if kind == 3 {
                ((value as f64 - binding.rest as f64) / (binding.full as f64 - binding.rest as f64))
                    .clamp(0.0, 1.0)
            } else {
                if value != 0 {
                    1.0
                } else {
                    0.0
                }
            };
            if action == "whammy" {
                if kind == 3 {
                    self.state.whammy = amount;
                } else {
                    self.whammy_pressed = amount > 0.5;
                }
            } else {
                self.state.buttons.insert(action.clone(), amount > 0.5);
            }
        }
    }

    pub fn tick(&mut self, seconds: f64) {
        if self
            .profile
            .bindings
            .get("whammy")
            .is_some_and(|b| b.kind == 1)
        {
            let speed = if self.whammy_pressed {
                1000.0 / self.profile.rise_ms
            } else {
                -1000.0 / self.profile.return_ms
            };
            self.state.whammy = (self.state.whammy + seconds * speed).clamp(0.0, 1.0);
        }
    }

    pub fn pressed(&self, action: &str) -> bool {
        self.state.buttons.get(action).copied().unwrap_or(false)
    }
    pub fn hat(&self) -> (i32, i32) {
        (
            self.pressed("right") as i32
                - (self.pressed("left") || (self.profile.ghwtde_extra_fix && self.pressed("extra")))
                    as i32,
            (self.pressed("down") || self.pressed("strum_down")) as i32
                - (self.pressed("up") || self.pressed("strum_up")) as i32,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn mapper(action: &str, kind: u16) -> Mapper {
        let mut m = Mapper::default();
        m.profile.bindings.insert(
            action.into(),
            Binding {
                source: "keyboard".into(),
                kind,
                code: 30,
                rest: 100,
                full: -100,
            },
        );
        m
    }
    #[test]
    fn separate_players_and_sources() {
        let mut a = mapper("green", 1);
        let b = mapper("green", 1);
        a.input("other", 1, 30, 1);
        assert!(!a.pressed("green"));
        a.input("keyboard", 1, 30, 1);
        assert!(a.pressed("green"));
        assert!(!b.pressed("green"));
        a.input("keyboard", 1, 30, 0);
        assert!(!a.pressed("green"));
    }
    #[test]
    fn spring_and_repeat() {
        let mut m = mapper("whammy", 1);
        m.input("keyboard", 1, 30, 2);
        m.tick(0.1);
        assert_eq!(m.state.whammy, 0.0);
        m.input("keyboard", 1, 30, 1);
        m.tick(0.125);
        assert_eq!(m.state.whammy, 0.5);
        m.tick(1.0);
        assert_eq!(m.state.whammy, 1.0);
        m.input("keyboard", 1, 30, 0);
        m.tick(0.09);
        assert!((m.state.whammy - 0.5).abs() < 0.001);
        m.reset();
        m.tick(0.1);
        assert_eq!(m.state.whammy, 0.0);
    }
    #[test]
    fn reversed_axis_clamps() {
        let mut m = mapper("whammy", 3);
        m.input("keyboard", 3, 30, 0);
        assert_eq!(m.state.whammy, 0.5);
        m.input("keyboard", 3, 30, -200);
        assert_eq!(m.state.whammy, 1.0);
        m.input("keyboard", 3, 30, 200);
        assert_eq!(m.state.whammy, 0.0);
    }
    #[test]
    fn shared_output_does_not_release_early() {
        let mut m = Mapper::default();
        m.state.buttons.insert("up".into(), true);
        m.state.buttons.insert("strum_up".into(), true);
        m.state.buttons.insert("up".into(), false);
        assert_eq!(m.hat(), (0, -1));
        m.state.buttons.insert("down".into(), true);
        assert_eq!(m.hat(), (0, 0));
    }
    #[test]
    fn invalid_profile_rejected() {
        let p = Profile {
            rise_ms: 0.0,
            ..Profile::default()
        };
        assert!(p.validate().is_err());
    }

    #[test]
    fn ghwtde_fix_routes_extra_to_dpad_left() {
        let mut m = mapper("extra", 1);
        m.profile.ghwtde_extra_fix = true;
        m.input("keyboard", 1, 30, 1);
        assert!(m.pressed("extra"));
        assert_eq!(m.hat(), (-1, 0));
        m.state.buttons.insert("right".into(), true);
        assert_eq!(m.hat(), (0, 0));
    }

    #[test]
    fn old_profile_defaults_extra_fix_to_disabled() {
        let profile: Profile =
            serde_json::from_str(r#"{"bindings":{},"rise_ms":250.0,"return_ms":180.0}"#).unwrap();
        assert!(!profile.ghwtde_extra_fix);
    }
}
