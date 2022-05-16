# Ink In Time

Appointment scheduling/booking applicaiton that aims to be super-simple, and open source!

- Easy docker deployment
- Few dependencies
- Timeblock detection through ical references
- Highly Configuraable (via yaml)
- No Log-in needed!
- Timezone selection

## Set Up

Copy `config/iit-example.yml` to `config/iit.yml`.

Install packages:

```shell
> pypi run python -m src.main
```

Run the server. If the configuration is incorrect, the server won't start.