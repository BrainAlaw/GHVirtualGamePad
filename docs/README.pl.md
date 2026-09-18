# GHVirtualGamePad — instrukcja

Dwie gitary USB działające jako klawiatury → dwa niezależne wirtualne pady. Każdy gracz wybiera odbiornik i uczy program przycisków. Whammy zero-jedynkowe jest zamieniane na płynnie zmieniającą się oś.

**[Instalatory i wydania](https://github.com/BrainAlaw/GHVirtualGamePad/releases)** · [Pełny README](../README.md)

## Status

0.2.0-rc.1 to kandydat do wydania stabilnego. Linux został sprawdzony przez właściciela na fizycznych gitarach. Windows ma rzeczywisty backend: sprawdzono wykrywanie klawiatur i dwa niezależne odczyty XInput. Pełny test dwóch gitar, blokowania oryginalnych klawiszy i gry na Windowsie pozostaje do wykonania.

## Linux / CachyOS

Rozpakuj archiwum Linux x86_64. W katalogu `ghvirtualgamepad` uruchom:

```bash
bash install.sh
```

Bez `sudo`. Program pojawi się w menu z ikoną. Python i Qt są w paczce; sam instalator potrzebuje systemowego Pythona 3.10+. Wymagane glibc 2.39+ i biblioteki graficzne pulpitu — aktualny CachyOS spełnia wymagania wersji glibc. To nie paczka dla Alpine.

Można też uruchamiać `app/GHVirtualGamePad` bez instalacji. Dotychczasowa wersja testowa nie wygasa. Instalacja jest wygodniejsza, ale nie jest warunkiem zapisu profili.

## Windows

Uruchom instalator `.exe`. Dodaje skróty i ikonę, proponuje brakujące **ViGEmBus** oraz **Interception**. Po instalacji sterowników zapisz pracę i zrestartuj komputer. Istniejące sterowniki nie są reinstalowane. Sam program nie wymaga administratora.

Interception instaluje systemowe filtry klawiatury i myszy. Nie wybieraj zwykłej klawiatury ani odbiornika współdzielonego z myszą. Warunki upstream dla jego binarnych składników dotyczą użytku niekomercyjnego; MIT projektu ich nie zastępuje.

Sterowniki są starszymi projektami, ViGEmBus nie jest już rozwijany. Nie gwarantujemy zgodności z każdą konfiguracją Windows 11. **Nie wyłączaj Secure Boot, integralności pamięci ani wymuszania podpisów**, jeżeli system blokuje sterownik. Instalator aplikacji nie ma podpisu Authenticode — sprawdź źródło i SHA-256.

Mapowania są zapisywane, ale na Windowsie odbiorniki trzeba wybrać przy każdym uruchomieniu: sloty Interception mogą się zmieniać. Po odłączeniu odbiornika zatrzymaj kontrolery i wybierz go ponownie. Windows nie łączy kilku slotów jednego odbiornika w jedno wejście.

## Mapowanie i gra

1. Ustaw gitary w trybie klawiatury. Obie mogą mieć sprzętowy Player 1, jeśli system widzi dwa urządzenia.
2. Wybierz odbiornik gracza 1. Na Linuxie w razie braku dostępu użyj **Enable device access**, zatwierdź polkit; w razie potrzeby podłącz odbiornik ponownie.
3. Kliknij element gitary, nazwę funkcji lub pole mapowania. Naciśnij i puść przycisk. Niepotrzebne funkcje mogą być puste.
4. Whammy przypisz jak przycisk. **Press (ms)** to czas wychylenia, **Return (ms)** — powrotu osi.
5. Powtórz dla gracza 2 z drugim odbiornikiem. Jedna gitara też działa.
6. **Save profiles**, puść wszystkie przyciski, następnie **Start controllers**.
7. Teraz uruchom/połącz Moonlight i przypisz kontrolery w grze.

Wyjście: progi A/B/Y/X/LB, strum D-pad góra/dół, Start/Back, Extra RB, whammy prawa oś Y. Linux tworzy gamepad uinput; Windows kontrolery XInput Xbox 360. Przy streamingu typ kontrolera po stronie gry zależy od hosta.

Przed zmianą mapowań zatrzymaj kontrolery. Zamknięcie aplikacji zwalnia urządzenia. Ctrl+Esc działa tylko z fokusem okna. Podgląd nie blokuje klawiszy — zamknij pola czatu/haseł podczas nauki.

## Zapis i aktualizacje

**Save profiles** pokazuje ścieżkę pliku poza katalogiem aplikacji. Linux: `profiles.json`, Windows: `windows-profiles.json`, symulator: `demo-profiles.json`. Przed aktualizacją zrób kopię. Kody wejść różnią się między systemami — Windows naucz osobno.

Linux zachowuje poprzednie wersje. Instalator Windows nie usuwa profili; deinstalator zostawia wspólne sterowniki. Diagnostyka nie zapisuje historii klawiszy, ale zawiera identyfikatory — przejrzyj ją przed publikacją.

Test akceptacyjny Windows: dwie gitary jednocześnie, kombinacje progów, oba kierunki strum, whammy, brak pisania klawiszy podczas gry, zatrzymanie/ponowny start i odłączenie odbiornika. Dopiero taki test zamknie etap release candidate.
