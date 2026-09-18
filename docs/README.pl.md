# GHVirtualGamePad — dokumentacja techniczna (PL)

Mapper oddzielnych klawiatur USB na niezależne wirtualne gamepady. Grafika gitary jest profilem interfejsu; nie wymagamy konkretnego modelu DOYO ani znanych wcześniej kodów klawiszy.

Warunek: system musi widzieć oddzielne odbiorniki/urządzenia wejściowe. Jeśli jeden odbiornik sprzętowo scala obie gitary w nierozróżnialny strumień tych samych klawiszy, program nie odtworzy informacji o graczu.

## Stan wersji 0.1

- Rust: dwa niezależne mapowania, cyfrowe whammy zamieniane na płynną oś, protokół JSON Lines, symulacja.
- Qt/QML z cienką warstwą PySide6: wybór gracza i urządzenia, klikalna gitara, nauka przypisań, podgląd, zapis, diagnostyka.
- Linux: grupowanie interfejsów USB przez sysfs, evdev, wyłączne przejmowanie przy Start, dwa urządzenia uinput, neutralizacja stanu po odłączeniu i reconnect w tym samym porcie.
- Konfiguracja dostępu przez przycisk w GUI i autoryzację polkit. GUI oraz backend działają jako użytkownik; nie wymagają stałego root ani usługi systemowej.
- Windows: **symulator**, bez odczytu osobnych fizycznych klawiatur i bez tworzenia padów Windows.

To wersja do testów sprzętowych, nie zatwierdzony produkt końcowy. Automatyczne testy nie potwierdzają zgodności z DOYO, SDL, Moonlight ani Guitar Hero. AppImage, instalator offline, własny sterownik Windows i samodzielna usługa systemd nie są jeszcze dostarczone.

## Windows — uruchomienie podglądu

Z katalogu projektu:

```powershell
.\run.ps1
```

Launcher instaluje Qt w lokalnym `.venv` i kompiluje backend. Wymaga Python 3.10–3.14 oraz Rust. W obecnym środowisku zostały przygotowane Python 3.11, Qt i Rust GNU; Rust nie został dodany do globalnego PATH przez instalator.

Wybierz Player 1, urządzenie A i `Demo bindings`. Dla Player 2 wybierz urządzenie B oraz jego `Demo bindings`. Klawiatura pulpitu steruje wyłącznie slotem otwartym w GUI — to symulacja dwóch fizycznych urządzeń. Kliknij `Focus keyboard`, użyj A/S/D/F/G i przytrzymaj Spację. Oba sloty korzystają z identycznego mechanizmu.

## CachyOS — paczka testowa

Przenieś `artifacts/ghvirtualgamepad-linux-x86_64.tar.gz` na Linux, rozpakuj i uruchom `bash launch.sh` w rozpakowanym katalogu. Paczka zawiera skompilowany backend Linux x86_64, GUI i konfigurator uprawnień. Nie potrzebuje Rust na komputerze docelowym. Pierwsze uruchomienie pobiera PySide6 do lokalnego środowiska Python, więc wymaga internetu.

Potrzebne są Python z obsługą venv/pip, sesja graficzna z bibliotekami Qt dla Wayland lub X11 oraz polkit z działającym agentem uwierzytelniania. W razie błędu zależności platformy Qt sprawdź standardowe biblioteki `libxcb`, `xcb-util-cursor`, `libxkbcommon` i `libegl` w systemie. Nie wyłączaj Secure Boot ani zabezpieczeń systemu.

Alternatywa z repozytorium: `bash run.sh` (wymaga Rust i narzędzi kompilacji). Tryb bez sprzętu: `bash run.sh --demo`.

### Pierwsze przypisanie

1. Obie gitary ustaw jako klawiatury / Player 1 na sprzęcie. W aplikacji będą osobnymi graczami.
2. Wybierz odbiornik dla Player 1. Jeśli odczyt jest zabroniony, kliknij `Enable device access` i zatwierdź konfigurację. Ponownie wybierz urządzenie; czasem potrzebne jest jego ponowne podłączenie.
3. Kliknij funkcję na gitarze lub liście, naciśnij i puść odpowiadający jej przycisk. Można pominąć niepotrzebne funkcje. Nauka ma limit 15 sekund.
4. Whammy przypisz jak przycisk. `Press (ms)` to czas od zera do pełnego wychylenia; `Return (ms)` to czas powrotu. Domyślnie 250/180 ms, niezależnie dla każdego gracza.
5. Powtórz dla Player 2, wybierając drugi odbiornik. Jednego urządzenia nie można przypisać do obu slotów. Jeden gracz również może działać samodzielnie.
6. Zapisz profile, puść przyciski i kliknij `START CONTROLLERS`. Dopiero potem uruchom Moonlight.
7. Na Windows hoście sprawdź dwa osobne pady, a następnie przypisz wejścia w Guitar Hero.

Podczas nauki wejście pozostaje dostępne dla pulpitu — używaj dedykowanego odbiornika, a nie klawiatury do pracy. Po Start aplikacja przejmuje wszystkie interfejsy wybranego odbiornika; nie wybieraj odbiornika współdzielonego z myszą lub główną klawiaturą. Stop lub zamknięcie aplikacji zwalnia urządzenia. Ctrl+Esc działa, gdy okno aplikacji ma fokus; nie jest globalnym skrótem Wayland.

Przy odłączeniu wyjście wraca do neutralnego stanu, a wirtualny pad pozostaje obecny. Powrót odbiornika do tego samego portu przywraca wejście. Przepięcie do innego portu wymaga ponownego wyboru i konfiguracji dostępu. Identyfikator zawiera VID/PID, numer seryjny, jeśli istnieje, i port — samo VID/PID nie rozróżnia dwóch takich samych gitar.

## Wyjście kontrolera

| Funkcja | Przycisk / oś pada |
|---|---|
| Green / Red / Yellow / Blue / Orange | A / B / Y / X / LB |
| Strum up/down | D-pad up/down |
| D-pad | D-pad |
| Start / Select / Extra | Start / Back / RB |
| Whammy | Right stick Y: 0 → +32767 → 0 |

Strum i D-pad są łączone logicznym OR; puszczenie jednego nie zwalnia drugiego. Kierunki przeciwne znoszą się. Wyjście używa standardowego układu evdev gamepada z identyfikatorem kompatybilnym z Xbox 360. Nie jest emulacją protokołu USB/XInput. Rozpoznanie przez SDL/Moonlight wymaga testu na docelowym Linuxie; w razie potrzeby należy dostarczyć wpis SDL GameController mapping. Kolejność utworzenia to Player 1, następnie Player 2, ale inne kontrolery hosta mogą wpływać na numery slotów gry.

## Dostęp i dane

Przycisk konfiguracji uruchamia `tools/setup_linux.py` przez pkexec. Skrypt weryfikuje VID/PID/port w sysfs i instaluje własną regułę `70-ghvirtualgamepad-*.rules` oraz `ghvirtualgamepad.conf` w modules-load.d. Reguła nadaje dostęp aktywnej sesji do wybranego odbiornika oraz uinput; dostęp do uinput pozwala tworzyć wirtualne urządzenia wejściowe. Nie nadaje dostępu do wszystkich fizycznych klawiatur. Wymagany jest systemd-logind/udev z obsługą `uaccess`.

Backend jest procesem potomnym GUI komunikującym się prywatnymi potokami, bez portu sieciowego. Zamknięcie potoku kończy backend. Reguły uprawnień pozostają po zamknięciu aplikacji. Nie są instalowane na Windowsie.

Profile są zapisywane atomowo w katalogu konfiguracji wskazywanym przez Qt. Symulacja korzysta z osobnego pliku. Zapis jest jawny (`Save profiles`). Diagnostyka eksportuje bieżące mapowanie i stan; nie rejestruje historii pisania, numerów seryjnych ani ścieżek urządzeń. Należy sprawdzić raport przed udostępnieniem, bo nazwy interfejsów wejściowych są częścią mapowania.

## Weryfikacja

```text
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test --locked
cargo build --locked
python -m unittest discover -s tests -v
python gui/app.py --demo --smoke-test
```

Testy obejmują izolację graczy, filtrowanie źródeł, powtórzenia klawiszy, łączenie D-pada/strum, syntetyczną oś, odwrócone osie, błędne profile, protokół procesu, zamknięcie potoku, mapowanie przez GUI i zapis/odczyt. CI jest przygotowane dla Windows i Linux; nie zostało uruchomione zdalnie.

Test sprzętowy: oba odbiorniki z tym samym VID/PID, kilka fretów + strum jednocześnie, długie przytrzymanie whammy, wyjęcie odbiornika podczas przytrzymania, reconnect, Stop, ponowne Start, zamknięcie GUI, brak zdublowanych klawiszy w Moonlight, dwa osobne kontrolery na hoście. Na razie testy te pozostają do wykonania na CachyOS.

## Budowanie paczki Linux na Windows

`tools/build-linux.ps1` buduje statyczny backend musl przy użyciu Rust GNU i rust-lld, bez WSL. Następnie `python tools/package_linux.py` tworzy archiwum testowe. Kompilacja krzyżowa nie zastępuje uruchomienia na Linuxie.

## Granice pierwszej wersji

- Ręczne przypisanie wejść; brak zgadywanego, fabrycznego profilu DOYO.
- Whammy cyfrowe z powrotem do zera. Odczyt osi dla kierunków jest dostępny, lecz pełny kreator kalibracji analogowej nie jest częścią tej wersji.
- Przełącznik czteropozycyjny można przypisywać, jeśli raportuje osobne klawisze lub kierunki osi. Przełącznik zmieniający tryb urządzenia wymaga ponownego wyboru po zmianie.
- Brak force feedback i automatycznej konfiguracji hosta Sunshine/Guitar Hero.
- VHF na Windows tworzy wirtualny HID, ale sam w sobie nie zapewnia XInput — wcześniejsze rozważania o takim zamienniku wymagają osobnego projektu i walidacji.
