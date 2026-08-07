# Dokumentacja Techniczna i Instrukcja Obsługi NEXUS OS

## 1. Wprowadzenie i Architektura

### Czym jest NEXUS OS

**NEXUS OS** to autorska platforma chmurowa klasy IaaS/VDI służąca do centralnego uruchamiania, zarządzania i udostępniania maszyn wirtualnych przez przeglądarkę. System łączy panel administracyjny, hipernadzorcę KVM/libvirt, webową konsolę noVNC, repozytorium ISO oraz narzędzia automatyzujące instalację i diagnostykę.

Platforma rozwiązuje typowe problemy środowisk IT:

- **Centralizacja danych**: systemy operacyjne i pliki robocze działają na serwerze, a nie na lokalnych komputerach użytkowników.
- **Praca na cienkich klientach**: użytkownik potrzebuje jedynie przeglądarki lub aplikacji NEXUS Capsule Manager.
- **Szybkie środowiska testowe**: administrator może tworzyć kapsuły VM, snapshoty, resetować stan i podmieniać nośniki ISO.
- **Kontrola kosztów**: moduł IAM i tokenomia NXC pozwalają rozliczać czas pracy maszyn.
- **Uproszczone Disaster Recovery**: panel, ISO, backupy i konfiguracja są odtwarzane z jednego pakietu instalacyjnego.

### Stos technologiczny

| Warstwa | Technologia |
| --- | --- |
| Backend API | **Python**, **FastAPI**, **Pydantic**, **Uvicorn** |
| Wirtualizacja | **KVM**, **QEMU**, **libvirt**, **qemu-img**, **virt-install** |
| Konsola VM | **noVNC**, **websockify**, WebSocket |
| Reverse proxy | **Nginx** |
| Certyfikaty | **Certbot / Let's Encrypt** |
| Storage plików | lokalny katalog `/var/lib/nexus`, opcjonalnie **MinIO** |
| Upload dużych plików | chunked uploads, konfiguracja Nginx bez limitu `413` |
| Diagnostyka | `nexusos-doctor.sh`, `journalctl`, `/var/log/nexus` |
| Interfejs | **Classic Core UI**, **AERO / Pure Snow**, statyczne HTML/JS/CSS |

### Główne komponenty

**NEXUS CORE**  
Klasyczny, ciemny panel operatora. Zawiera dashboard, terminal, procesy, pliki, Hyper-Deck, admin/IAM, media, BBS, Kanban, pogodę, newsy i narzędzia diagnostyczne.

**AERO / Pure Snow**  
Nowoczesny jasny panel użytkownika i operatora. Docelowo jest rekomendowany jako domyślny widok komercyjny, ponieważ ma czytelniejszą hierarchię i spokojniejszy układ.

**Hyper-Deck**  
Moduł sterowania maszynami wirtualnymi: tworzenie VM, start, ACPI shutdown, hard reset, snapshot, konfiguracja, logi, port forwarding, ISO Vault, sterowniki VirtIO i konsola noVNC.

**ISO Vault**  
Magazyn obrazów ISO, qcow2 i nośników instalacyjnych. Obsługuje duże pliki przez upload w kawałkach oraz bezpieczne katalogi dostępne dla procesu QEMU.

**IAM / Admin**  
Zarządzanie użytkownikami, rolami, hasłami, tokenami rozliczeniowymi, logami logowania oraz akcjami administracyjnymi.

**NEXUS Capsule Manager**  
Aplikacja Windows dostępna z katalogu `static/downloads`, przeznaczona do pracy z NEXUS OS i kapsułami.

## 2. Przewodnik Administratora

### Wymagania serwera

Minimalne wymagania panelu:

- Linux z Pythonem 3.
- 2 GB RAM.
- 10 GB wolnego miejsca.
- Otwarty port `9090` lub reverse proxy Nginx na `80/443`.

Rekomendowane wymagania dla pełnej wirtualizacji:

- CPU z obsługą wirtualizacji sprzętowej: **Intel VT-x** albo **AMD-V**.
- Dostęp do `/dev/kvm`.
- 8 GB RAM lub więcej.
- 80 GB wolnego miejsca lub więcej na `/var/lib/libvirt/images`.
- System z systemd: Debian, Ubuntu, Proxmox, Rocky, Alma, Fedora, Arch lub openSUSE.
- VPS/dedyk z włączoną wirtualizacją zagnieżdżoną, jeśli NEXUS działa wewnątrz innej VM.

Sprawdzenie KVM:

```bash
ls -l /dev/kvm
egrep -c '(vmx|svm)' /proc/cpuinfo
```

### Instalacja pełna

Pełna instalacja jest przeznaczona dla świeżego VPS-a lub serwera dedykowanego. Instaluje panel, hipernadzorcę, Nginx, noVNC, OVMF, swtpm, MinIO, rclone, narzędzia sieciowe i diagnostyczne.

```bash
tar -xzf nexusos-linux-installer.tar.gz
cd nexusos_linux_package
sudo bash install_everything.sh --domain nexusos.pl
```

Instalacja z próbą wystawienia HTTPS przez Let's Encrypt:

```bash
sudo bash install_everything.sh --domain nexusos.pl --issue-cert admin@example.com
```

Najważniejsze flagi `install_everything.sh`:

| Flaga | Znaczenie |
| --- | --- |
| `--domain nexusos.pl` | Ustawia publiczną domenę i konfigurację Nginx. |
| `--issue-cert EMAIL` | Próbuje wystawić certyfikat Let's Encrypt przez Certbot. |
| `--prefix /opt/nexusos` | Zmienia katalog instalacji aplikacji. |
| `--port 9090` | Ustawia port backendu FastAPI. |
| `--bind 0.0.0.0` | Ustawia adres nasłuchu backendu. |
| `--admin-password HASLO` | Ustawia początkowe hasło administratora. |
| `--no-minio` | Pomija instalację MinIO. |
| `--no-systemd` | Nie tworzy usług systemd. |

### Instalacja standardowa

Standardowy instalator pozwala precyzyjniej kontrolować zakres instalacji.

Panel z hipernadzorcą i Nginx:

```bash
sudo bash install.sh --with-hypervisor --with-nginx --domain nexusos.pl
```

Sam panel bez pełnej warstwy VM:

```bash
sudo bash install.sh
```

Najważniejsze flagi `install.sh`:

| Flaga | Znaczenie |
| --- | --- |
| `--with-hypervisor` | Instaluje QEMU, libvirt, virt-install, noVNC/websockify. |
| `--with-nginx` | Instaluje i konfiguruje reverse proxy Nginx. |
| `--domain DOMENA` | Ustawia domenę publiczną. |
| `--admin-password HASLO` | Zapisuje początkowe hasło administratora. |
| `--no-systemd` | Pomija usługę systemd. |

### Struktura katalogów

| Ścieżka | Opis |
| --- | --- |
| **`/opt/nexusos/app`** | Kod backendu, interfejsy webowe i pliki statyczne. |
| **`/opt/nexusos/venv`** | Środowisko Python virtualenv. |
| **`/etc/nexusos/nexusos.env`** | Główna konfiguracja środowiskowa usługi. |
| **`/var/lib/nexus/iso_storage`** | Główny magazyn ISO, qcow2, OpenCore i obrazów instalacyjnych. |
| **`/var/lib/nexus/upload_tmp`** | Tymczasowe katalogi uploadów chunked. |
| **`/var/lib/libvirt/images`** | Domyślny katalog dysków VM libvirt. |
| **`/var/lib/libvirt/images/nexus-isos`** | Katalog ISO widoczny dla QEMU/libvirt. |
| **`/var/log/nexus`** | Logi aplikacyjne i diagnostyczne NEXUS OS. |
| **`/var/backups/nexusos`** | Backupy panelu i backupy całego serwera. |
| **`/var/lib/nexus/minio`** | Dane MinIO, jeśli pełny instalator go uruchomił. |

### Konfiguracja środowiskowa

Główna konfiguracja znajduje się w:

```bash
/etc/nexusos/nexusos.env
```

Przykład:

```bash
NEXUS_BIND=0.0.0.0
NEXUS_PORT=9090
NEXUS_PUBLIC_URL=https://nexusos.pl
NEXUS_BACKUP_DIR=/var/backups/nexusos
NEXUS_LIBVIRT_IMAGE_DIR=/var/lib/libvirt/images
NEXUS_ISO_STORAGE_DIR=/var/lib/nexus/iso_storage
NEXUS_UPLOAD_TMP_DIR=/var/lib/nexus/upload_tmp
NEXUS_LOG_DIR=/var/log/nexus
NEXUS_MAX_VM_UPLOAD_BYTES=85899345920
RCLONE_CONFIG=/root/.config/rclone/rclone.conf
```

Po zmianie konfiguracji:

```bash
sudo systemctl restart nexusos
```

### Zarządzanie usługą

Status:

```bash
systemctl status nexusos --no-pager
```

Logi na żywo:

```bash
journalctl -u nexusos -f
```

Restart:

```bash
sudo systemctl restart nexusos
```

Jeśli systemd nie jest używany:

```bash
/opt/nexusos/run-nexusos.sh
```

### Nginx i błąd 413

Szablon Nginx dostarczony z pakietem ustawia:

```nginx
client_max_body_size 0;
```

To eliminuje problem:

```text
413 Request Entity Too Large
```

Dodatkowo backend używa uploadów chunked i limitu:

```bash
NEXUS_MAX_VM_UPLOAD_BYTES=85899345920
```

### MinIO Object Storage

Pełny instalator instaluje MinIO, chyba że użyto `--no-minio`.

Adresy:

```text
API:     http://SERVER_IP:9000
Console: http://SERVER_IP:9001
Env:     /etc/nexusos/minio.env
Data:    /var/lib/nexus/minio
```

Status:

```bash
systemctl status nexus-minio --no-pager
```

Dane logowania są generowane lokalnie i zapisane w:

```bash
/etc/nexusos/minio.env
```

### Kopie zapasowe

NEXUS OS posiada dwa poziomy backupów:

- **Backup panelu**: zapisuje pliki aplikacji, konfigurację i dane panelu.
- **Backup serwera**: archiwizuje wybrane części hosta, np. katalogi NEXUS, konfigurację i ścieżki VM.

Rekomendacje:

- Twórz backup po pierwszym poprawnym uruchomieniu systemu.
- Nie traktuj lokalnego backupu jako jedynej kopii. Wysyłaj kopie poza VPS.
- Dla VM używaj snapshotów i osobnych kopii katalogu **`/var/lib/libvirt/images`**.
- Przed dużą zmianą w VM wykonaj snapshot w Hyper-Deck.

Przykładowy zewnętrzny backup przez `rsync`:

```bash
rsync -avP /var/backups/nexusos/ root@BACKUP_HOST:/backup/nexusos/
rsync -avP /var/lib/nexus/ root@BACKUP_HOST:/backup/nexus-data/
```

### Aktualizacja NEXUS OS

Procedura aktualizacji:

1. Skopiuj nową paczkę na serwer.
2. Wykonaj backup panelu i danych.
3. Rozpakuj paczkę.
4. Uruchom instalator ponownie.

```bash
tar -xzf nexusos-linux-installer.tar.gz
cd nexusos_linux_package
sudo bash install_everything.sh --domain nexusos.pl
```

Instalator tworzy kopię poprzedniego katalogu aplikacji:

```text
/opt/nexusos/app.backup.YYYYMMDD-HHMMSS
```

### Disaster Recovery po utracie VPS-a

Minimalna procedura odtworzenia:

1. Zamów nowy VPS/dedyk z włączonym KVM.
2. Skieruj DNS `nexusos.pl` na nowy adres IP.
3. Wgraj `nexusos-linux-installer.tar.gz`.
4. Uruchom pełny instalator:

```bash
sudo bash install_everything.sh --domain nexusos.pl --issue-cert admin@example.com
```

5. Przywróć dane:

```bash
rsync -avP backup/nexus-data/ /var/lib/nexus/
rsync -avP backup/libvirt-images/ /var/lib/libvirt/images/
rsync -avP backup/nexusos-backups/ /var/backups/nexusos/
```

6. Zrestartuj usługę:

```bash
sudo systemctl restart nexusos
```

7. Uruchom diagnostykę:

```bash
/opt/nexusos/bin/nexusos-doctor.sh
```

## 3. Instrukcja Obsługi Panelu NEXUS CORE

### Logowanie

Domyślnie panel jest dostępny pod:

```text
http://SERVER_IP:9090/
https://nexusos.pl/
```

Panel AERO:

```text
https://nexusos.pl/static/aero.html
```

Po pierwszym logowaniu:

1. Wejdź w **Admin/IAM**.
2. Zmień hasło administratora.
3. Dodaj użytkowników.
4. Nadaj role i limity.

### Role użytkowników

Rekomendowany model ról:

- **Admin**: pełna kontrola, VM, backupy, użytkownicy, tokeny, konfiguracja.
- **Operator**: obsługa VM, ISO, logów i podstawowych akcji serwisowych.
- **User**: dostęp do przypisanych kapsuł, plików i konsoli.
- **Read-only**: podgląd bez prawa edycji.

Każda akcja administracyjna powinna być traktowana jako operacja audytowalna. Logi logowania i akcje należy okresowo przeglądać w panelu Admin.

### Hyper-Deck: tworzenie kapsuły VM

Typowy przepływ:

1. Otwórz **Hyper-Deck** albo **VM**.
2. Wybierz profil systemu: Windows, Linux, BSD, legacy albo BYOL.
3. Wybierz obraz ISO z **ISO Vault**.
4. Ustaw RAM, vCPU i rozmiar dysku.
5. Dla Windows wybierz sterowniki VirtIO, jeśli są wymagane.
6. Kliknij utworzenie VM.
7. Po starcie kliknij **Otwórz konsolę**.

Rekomendowane ustawienia:

| System | RAM | vCPU | Uwagi |
| --- | --- | --- | --- |
| Windows XP/98/95 | 256-1024 MB | 1 | Profil legacy, starszy CPU, ostrożnie z ACPI. |
| Windows 7 | 2-4 GB | 1-2 | VirtIO opcjonalnie, zależnie od ISO. |
| Windows 10/11 | 4-8 GB | 2-4 | VirtIO, UEFI, TPM dla Windows 11. |
| Linux Server | 512 MB-2 GB | 1-2 | Najlepszy kandydat na thin provisioning. |
| macOS/OpenCore | zależnie od wersji | 2+ | Wyłącznie BYOL, wymagany własny bootloader/media. |

### Zarządzanie kapsułą

Najważniejsze akcje:

- **POWER ON**: uruchamia VM.
- **ACPI SHUTDOWN**: miękkie zamknięcie systemu.
- **HARD RESET**: twardy reset, używać ostrożnie.
- **SNAPSHOT**: zapisuje migawkę stanu.
- **CONFIG**: edycja RAM, vCPU, ISO, dysku i sieci.
- **LOGI**: ostatnie logi libvirt/QEMU.
- **PORTY**: reguły port forwarding.
- **USUŃ VM**: usuwa VM, operacja destrukcyjna.

Przed instalacją sterowników, aktualizacją systemu lub testem podejrzanego oprogramowania zawsze wykonaj snapshot.

### Konsola noVNC

Konsola VM działa w przeglądarce i pozwala obsługiwać maszynę przed startem systemu operacyjnego, również na poziomie BIOS/UEFI.

Typowe przyciski konsoli:

- **FIT**: dopasowanie obrazu do okna.
- **AUTO**: automatyczne skalowanie.
- **CENTRUJ**: wyśrodkowanie obrazu.
- **ROZMIAR**: ręczne ustawienie rozdzielczości/obszaru widoku.
- **FULLSCREEN**: pełny ekran.
- **MYSZ ON**: przekierowanie myszy do konsoli.
- **RESET MYSZY**: naprawa rozjechanego kursora.
- **KURSOR PRECYZYJNY**: tryb dokładniejszego sterowania.
- **KLAWIATURA**: wysuwana klawiatura ekranowa.
- **FOCUS**: przekierowanie myszy i klawiatury do VM.
- **CTRL+ALT+DEL**: wysłanie sekwencji do VM.
- **ISO**: szybkie okno montowania nośnika.
- **ZAMKNIJ**: zamknięcie widoku konsoli.

Jeśli kursor działa słabo:

1. Kliknij **RESET MYSZY**.
2. Włącz **MYSZ ON**.
3. Użyj **FOCUS**.
4. Dla nowej VM upewnij się, że XML zawiera tablet USB/input tablet.

### Clipboard i wklejanie tekstu

Do prostych komend używaj pola wklejania w konsoli:

1. Wklej tekst do pola schowka.
2. Kliknij **WKLEJ** albo **WPISZ**.
3. Jeśli system gościa nie obsługuje wspólnego schowka, funkcja może działać jako symulowane wpisywanie klawiaturą.

W systemach Windows pełny clipboard wymaga odpowiednich dodatków gościa lub agenta. W systemach Linux najlepsze efekty daje QEMU Guest Agent albo integracja SPICE/VNC zależna od obrazu.

### ISO Vault

ISO Vault służy do przechowywania:

- obrazów instalacyjnych `.iso`,
- obrazów dysków `.qcow2`,
- OpenCore `.qcow2`,
- sterowników VirtIO,
- narzędzi recovery.

Główna ścieżka:

```bash
/var/lib/nexus/iso_storage
```

Szybki upload administracyjny:

```bash
rsync -avP ./isos/ root@SERVER:/var/lib/nexus/iso_storage/
```

Po wgraniu plików odśwież ISO Vault w panelu.

### BYOL dla macOS/OpenCore

NEXUS OS działa w modelu **Bring Your Own License**.

System:

- nie dostarcza licencji Apple,
- nie dostarcza OSK/SMC,
- nie dostarcza chronionych komponentów Apple,
- udostępnia wyłącznie infrastrukturę do uruchomienia legalnie posiadanych nośników użytkownika.

Przed uruchomieniem profilu Cupertino/macOS użytkownik musi potwierdzić BYOL.

Wymagane elementy po stronie użytkownika:

- własny legalny obraz instalacyjny,
- własny bootloader OpenCore,
- zgodność licencyjna po stronie organizacji.

Przykładowe miejsce na OpenCore:

```bash
/var/lib/nexus/iso_storage/opencore.qcow2
```

### Tokenomia NXC

Moduł billingowy służy do rozliczania czasu i zasobów VM.

Typowe zasady:

- VM w stanie **running** zużywa tokeny.
- VM w stanie **stopped** nie zużywa CPU/RAM, ale nadal zajmuje miejsce dyskowe.
- VM w stanie **suspended** może mieć osobną stawkę zależną od polityki.

Administrator powinien regularnie kontrolować:

- salda użytkowników,
- właścicieli VM,
- uruchomione kapsuły,
- nieaktywne VM zużywające zasoby.

### Moduły plikowe i użytkowe

NEXUS OS zawiera dodatkowe moduły:

- **Pliki**: podstawowy eksplorator plików.
- **Media Deck**: prywatny streaming audio/wideo z katalogów serwera.
- **Visual Archive**: galeria zdjęć i przechwytów.
- **Secure Drop**: udostępnianie plików linkiem.
- **BBS**: tablica społecznościowa.
- **Kanban**: tablica operacyjna.
- **News / Pogoda / Radio / Gry**: moduły informacyjne i użytkowe.
- **Cloud Drive / rclone**: integracja z dyskami zewnętrznymi, np. Google Drive.

## 4. Narzędzia i Diagnostyka

### nexusos-doctor.sh

Pełny instalator tworzy skrypt:

```bash
/opt/nexusos/bin/nexusos-doctor.sh
```

Uruchomienie:

```bash
sudo /opt/nexusos/bin/nexusos-doctor.sh
```

Skrypt sprawdza:

- działające usługi NEXUS/libvirt/nginx/MinIO,
- odpowiedź API,
- listę VM z `virsh`,
- wolne miejsce na dyskach,
- pamięć RAM,
- moduły KVM,
- zawartość ISO storage.

### Logi systemowe

Logi usługi:

```bash
journalctl -u nexusos -n 100 --no-pager
journalctl -u nexusos -f
```

Logi Nginx:

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

Logi NEXUS:

```bash
ls -lah /var/log/nexus
```

Logi VM QEMU/libvirt:

```bash
ls -lah /var/log/libvirt/qemu/
tail -n 80 /var/log/libvirt/qemu/NAZWA_VM.log
```

### Najczęstsze problemy

#### Panel nie odpowiada

Sprawdź usługę:

```bash
systemctl status nexusos --no-pager
journalctl -u nexusos -n 100 --no-pager
```

Sprawdź port:

```bash
ss -ltnp | grep 9090
```

Restart:

```bash
sudo systemctl restart nexusos
```

#### Nginx pokazuje 502

Najczęstsza przyczyna: backend FastAPI nie działa albo działa na innym porcie.

```bash
curl -v http://127.0.0.1:9090/
systemctl status nexusos --no-pager
nginx -t
```

Po naprawie:

```bash
sudo systemctl restart nexusos
sudo systemctl reload nginx
```

#### Upload dużego ISO kończy się błędem 413

Sprawdź konfigurację Nginx:

```bash
grep -R "client_max_body_size" /etc/nginx/
```

Powinno być:

```nginx
client_max_body_size 0;
```

Potem:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### VM nie startuje: brak KVM

Sprawdź:

```bash
ls -l /dev/kvm
lsmod | grep kvm
egrep -c '(vmx|svm)' /proc/cpuinfo
```

Jeśli `/dev/kvm` nie istnieje, dostawca VPS może nie wspierać wirtualizacji zagnieżdżonej. W takim przypadku pełny Hyper-Deck nie uruchomi VM, chociaż panel webowy nadal może działać.

#### VM nie widzi ISO

Sprawdź, czy plik istnieje:

```bash
ls -lah /var/lib/nexus/iso_storage
ls -lah /var/lib/libvirt/images/nexus-isos
```

Sprawdź uprawnienia:

```bash
chmod -R 755 /var/lib/nexus/iso_storage
chmod -R 755 /var/lib/libvirt/images/nexus-isos
```

Sprawdź log VM:

```bash
tail -n 100 /var/log/libvirt/qemu/NAZWA_VM.log
```

#### Brak miejsca na dysku

Sprawdź:

```bash
df -h
du -h -d 1 /var/lib/libvirt/images | sort -h
du -h -d 1 /var/lib/nexus | sort -h
```

Możliwe działania:

- usuń nieużywane ISO,
- usuń stare snapshoty,
- przenieś backupy poza VPS,
- użyj thin provisioning qcow2,
- wykonaj TRIM/fstrim wewnątrz VM, jeśli system gościa to wspiera.

#### Windows 11 wymaga TPM/UEFI

Windows 11 najczęściej wymaga:

- UEFI/OVMF,
- TPM przez `swtpm`,
- odpowiedniego profilu CPU,
- wystarczającej ilości RAM.

Pełny instalator próbuje doinstalować `ovmf` i `swtpm`, ale dostępność pakietów zależy od dystrybucji.

#### Legacy Windows 95/98/XP ma błędy instalacji

Rekomendacje:

- 1 vCPU,
- niski RAM: 256-512 MB dla Windows 9x,
- starszy model CPU,
- ostrożnie z ACPI,
- preferuj IDE/SATA zamiast nowych kontrolerów,
- wykonaj snapshot przed każdym etapem instalacji.

#### macOS/OpenCore pokazuje tylko EFI albo nie widzi instalatora

Sprawdź:

- czy OpenCore jest poprawnym qcow2,
- czy instalator jest podpięty jako osobny nośnik,
- czy profil VM używa UEFI/Q35,
- czy media są dostępne dla procesu QEMU,
- czy konfiguracja OpenCore zawiera sterowniki skanowania partycji, np. OpenPartitionDxe/HfsPlus zależnie od wersji.

Pamiętaj: NEXUS nie dostarcza chronionych komponentów Apple. Operator odpowiada za legalność i kompletność własnych nośników.

### Komendy administracyjne libvirt

Lista VM:

```bash
virsh list --all
```

Start VM:

```bash
virsh start NAZWA_VM
```

Miękkie wyłączenie:

```bash
virsh shutdown NAZWA_VM
```

Twarde zatrzymanie:

```bash
virsh destroy NAZWA_VM
```

XML VM:

```bash
virsh dumpxml NAZWA_VM > vm.xml
```

Logi:

```bash
tail -f /var/log/libvirt/qemu/NAZWA_VM.log
```

### Zasady bezpieczeństwa operacyjnego

- Nie wystawiaj portu `9090` publicznie bez Nginx/HTTPS i silnego hasła.
- Po instalacji natychmiast zmień hasło administratora.
- Włącz firewall hosta.
- Trzymaj ISO i backupy poza katalogami publicznymi.
- Operacje destrukcyjne, takie jak usuwanie VM lub dysku, powinny wymagać potwierdzenia.
- Regularnie przeglądaj logi logowania.
- Nie przechowuj licencji, kluczy prywatnych ani tajnych tokenów w publicznych katalogach panelu.
- Dla środowisk klientów używaj separacji sieciowej i reguł deny-by-default.

## 5. Szybka karta operacyjna

Instalacja pełna:

```bash
sudo bash install_everything.sh --domain nexusos.pl --issue-cert admin@example.com
```

Status:

```bash
systemctl status nexusos --no-pager
```

Logi:

```bash
journalctl -u nexusos -f
```

Diagnostyka:

```bash
/opt/nexusos/bin/nexusos-doctor.sh
```

Restart:

```bash
sudo systemctl restart nexusos
```

ISO storage:

```bash
/var/lib/nexus/iso_storage
```

Dyski VM:

```bash
/var/lib/libvirt/images
```

Panel:

```text
https://nexusos.pl/
https://nexusos.pl/static/aero.html
```

Backup:

```bash
/var/backups/nexusos
```

## 6. Załącznik: pliki instalacyjne w paczce

| Plik | Opis |
| --- | --- |
| **`install_everything.sh`** | Pełny instalator świeżego VPS-a. |
| **`install.sh`** | Standardowy instalator kontrolowany flagami. |
| **`uninstall.sh`** | Deinstalator z opcjonalnym `--purge`. |
| **`requirements.txt`** | Zależności Pythona. |
| **`systemd/nexusos.service`** | Szablon usługi systemd. |
| **`nginx/nexusos.conf.example`** | Szablon reverse proxy. |
| **`app/server.py`** | Backend NEXUS OS. |
| **`app/static/index.html`** | Classic Core UI. |
| **`app/static/aero.html`** | AERO / Pure Snow UI. |
| **`app/static/downloads`** | Instalatory NEXUS Capsule Manager dla Windows. |

Dokumentacja ta opisuje stan pakietu instalacyjnego NEXUS OS przygotowanego do odtworzenia platformy po utracie VPS-a oraz do wdrożeń na nowych serwerach Linux.
