# Auto mode

Automatically switch macOS dark / light mode based on sunrise / sunset

## Install

```
pip install auto-mode
```

## Usage

Add to cron (crontab -e)
```
*/5 * * * * auto-mode 2>&1 >/dev/null
```
