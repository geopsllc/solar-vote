# Vote Monitoring Tool for the Solar Network

## Installation

Basic install:
```sh
git clone https://github.com/geopsllc/solar-vote
cd solar-vote
bash install.sh
nano config.py
```
- change config.py to your liking
- test the script in cli mode by running ```python3 svote.py```

Frontend setup:
- add a crontab entry (```crontab -e```) to run the script every minute:
```* * * * * cd $HOME/solar-vote && python3 svote.py > /dev/null 2>&1```
- install and setup a webserver (apache/nginx) to serve folder web

## General

This is a Multi-Address Vote Monitoring Tool for the Solar Network.
- Supports Solar Core v3+.
- Requires Python 3.8 or above - native on Ubuntu 20.04.
- You can use it in cli mode or bring up a web interface that refreshes every minute.
- Does not support addresses voting for multiple delegates.

## Changelog

### 0.2

- logic rewrite to consider total rewards instead of per-address rewards
- added async logic to speed up api queries

### 0.1

- initial release

## Security

If you discover a security vulnerability within this package, please open an issue. All security vulnerabilities will be promptly addressed.

## Credits

- [All Contributors](../../contributors)
- [Georgi Stoyanov](https://github.com/geopsllc)

## License

- [MIT](LICENSE) © [geopsllc](https://github.com/geopsllc)
