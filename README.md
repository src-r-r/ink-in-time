# Ink In Time

Appointment scheduling/booking application that aims to be super-simple, and open source!

- Privacy-friendly
- Easy docker deployment
- Few dependencies
- Timeblock detection through ical references
- Highly Configurable (via yaml)
- No Log-in needed!
- Timezone selection
- `block/YYY/MM/DD` selection to make appointment choosing easy
  ("Choose a time to meet tomorrow" → `30min/2022/9/30` )

## Set Up

Copy `config/iit-example.yml` to `config/iit.yml`.

Install packages:

```shell
> pypi run python -m src.main
```

Run the server. If the configuration is incorrect, the server won't start.


## Testing

### Running the tests

> Hint: it's **HIGHLY** recommended you pull from an ics mock server. See below.

```
> pypi run pytest src/tests.py
```

Since the server runs a background process to compile the time blocks,
sometimes this will result in a failure. See the debug messages for details.
This usually involves a race condition to detect that the `.compilepid` has
been created.
### Mock Server

The mock server uses `node-mock-server` to serve ICS files at `localhost:5002/ics`.

To use the mock server, do the following:

```shell
> npm i
> npm run ics # starts the ICS mock server.
```

Go to `localhost:5002/ui` if it isn't open already. There you see the endpoints

Copy one of those endpoints to the `calendars` configuration.

Just keep the server up and you'll pull from those endpoints for testing!

Note you will see errors from `icalendar` during the compilation process. These can be ignored.

> **WARNING**: Any data you place in the `mocking` directory will be commited to git!
> A safer directory is `mock_data`, which is ignored.

### Generating Mock icals

To generate your own mock data, run:

```shell
> pypi -m main.fakeics
```

The data is stored in `<project_dir>/mock_data/ics/<funny-name>.ics`.

The files can then be copied to new endpoints if you wish.