# telegram-video-forwarder

Arşiv kanalındaki videoları 5 ayrı Telegram kanalına, günlük ve
benzersiz şekilde dağıtan otomasyon. GitHub Actions üzerinde çalışır,
bu yüzden bilgisayar kapalıyken de kendiliğinden devam eder. Ücretsizdir.

Repo: https://github.com/depofiti-design/telegram-video-forwarder (private)

## Kanallar

| Rol | Kanal | Chat ID |
|---|---|---|
| Kaynak (arşiv) | arşivvv | `-1004449450721` |
| Hedef 1 | NE KADAR GÜZEL | `-1003965787626` |
| Hedef 2 | GUZEL VIDEOLAR :) | `-1003336352400` |
| Hedef 3 | NERELERE GELDİK :) | `-1003907423237` |
| Hedef 4 | 1.8 VIP SİNEMA :) | `-1003924824277` |
| Hedef 5 | MUTLULUK KAYNAĞI | `-1003919149618` |

Kullanılan bot: `@arsivyonetim_bot` — kaynak ve 5 hedef kanalın hepsinde admin olması gerekir.

## Nasıl çalışır

- `.github/workflows/forward.yml`, Türkiye saatine göre günde 11 kez tetiklenir:
  09:00, 10:30, 12:00, 14:00, 15:30, 17:00, 18:30, 20:30, 22:30, 00:30, 02:30.
  (Pencereler: sabah-öğlen 3, öğlen-akşam 3, akşam 18:00-gece 03:00 arası 5 gönderim.)
- Her tetiklemede `send.py`, **5 hedef kanalın her birine 1 video** gönderir
  (`copyMessage` ile — "forwarded from" etiketi görünmez, kaynak kanal gizli kalır).
- Gönderilecek video, o gün henüz hiçbir kanala gitmemiş videolar arasından,
  en az kullanılan / en uzun süredir kullanılmayan öncelikli olacak şekilde seçilir.
  **Aynı video aynı gün içinde 2. bir kanala gitmez**, farklı bir günde tekrar
  kullanılabilir ve başka bir kanala gidebilir.
- Kullanım geçmişi `state.json` içinde tutulur ve her çalıştırma sonunda
  otomatik commit'lenir.
- Küçük bir rastgele bekleme (0-8 dk) eklenir, gönderimler saat başı gibi
  robotik durmasın diye.

## Yeni video ekleme

Kaynak kanala (arşivvv) yeni video eklemen yeterli — hiçbir şey söylemene
gerek yok. Her çalıştırmada script, daha önce görülmemiş yeni mesaj ID'lerini
otomatik tarar (`send.py` içindeki `incremental_scan`) ve havuza ekler.

## İlk kurulum (backfill)

`discover.py`, kaynak kanaldaki tüm videoları tek seferlik tarayıp
`state.json`'ı oluşturdu (999 video bulundu, id 1-999 arası). Bu script bir
daha çalıştırılmasına gerek yok, sadece referans için repoda duruyor.

## Gizli bilgiler (GitHub Secrets)

- `BOT_TOKEN` — bot API token'ı
- `SOURCE_CHANNEL_ID` — kaynak kanal ID'si
- `TARGET_CHANNEL_IDS` — 5 hedef kanal ID'si, virgülle ayrılmış
- `STAGING_CHAT_ID` — yeni video taraması için kullanılan, botu başlatmış
  olan kişisel hesabın private chat ID'si (test/tarama amaçlı, gönderim
  yapılmaz, sadece kopyala-sil ile varlık kontrolü yapılır)

## Sıklığı / kanalları değiştirmek

- Saatleri değiştirmek için `.github/workflows/forward.yml` içindeki
  `cron` satırlarını düzenle (UTC, TR saatinden 3 saat geri).
- Kanal eklemek/çıkarmak için `TARGET_CHANNEL_IDS` secret'ını güncelle.