# 📂 Configuration

## Config file location

Your config file is located at the directory you were when you first run LNXlink. This can be anything you write like of the `config.yaml` that I suggested. You can find where it is from the systemd service:

{% tabs %}
{% tab title="Desktop" %}
```
cat ~/.config/systemd/user/lnxlink.service | grep -i ExecStart
```
{% endtab %}

{% tab title="Server" %}
```
cat /etc/systemd/lnxlink.service | grep -i ExecStart
```
{% endtab %}
{% endtabs %}

## Modules

By default all modules are automatically loaded. This happens when the modules section is empty like this:

```yaml
modules:
```

You should select the ones you want to load. All supported modules can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and the configuration should look like this:

```yaml
modules:
- notify
- camera_used
- idle
- keep_alive
- shutdown
- brightness
```

## Custom module

You can create custom modules and import them to your configuration with their full path. The name has to be unique so that it won't conflict with another python library.

Code examples can be found [here](https://github.com/bkbilly/lnxlink/blob/master/lnxlink/modules) and this is how to add the `mytest` module to your configuration.

```yaml
custom_modules:
- /home/user/mytest.py
```

3rd party custom modules:

* [https://github.com/PW999/lnxlink\_gpu\_nvidia\_settings](https://github.com/PW999/lnxlink\_gpu\_nvidia\_settings)
* [https://github.com/bkbilly/lnxlink/discussions/81](https://github.com/bkbilly/lnxlink/discussions/81)

## Exclude Modules

In case you have empty modules config which auto loads all the available modules, you can have this option that excludes modules from auto loading:

```yaml
exclude:
- screenshot
- webcam
```
