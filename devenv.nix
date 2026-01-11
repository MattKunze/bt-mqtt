{ pkgs, lib, config, inputs, ... }:

{
  packages = [
    pkgs.postgresql_16
    pkgs.mosquitto  # MQTT client tools (mosquitto_pub, mosquitto_sub)
    pkgs.mqttui
  ];

  # https://devenv.sh/languages/
  languages.javascript.enable = true;
  languages.javascript.npm.enable = true;
  languages.python.enable = true;
  languages.python.uv.enable = true;

  # https://devenv.sh/services/
  services.postgres = {
    enable = true;
    package = pkgs.postgresql_16;
    initialDatabases = [{ name = "bt_mqtt"; }];
    initialScript = ''
      CREATE USER btmqtt WITH PASSWORD 'btmqtt_dev';
      GRANT ALL PRIVILEGES ON DATABASE bt_mqtt TO btmqtt;
    '';
    listen_addresses = "127.0.0.1";
    port = 5432;
  };
}
