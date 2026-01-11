{ pkgs, lib, config, inputs, ... }:

{
  packages = [ ];

  # https://devenv.sh/languages/
  languages.javascript.enable = true;
  languages.javascript.npm.enable = true;
  languages.python.uv.enable = true;
}
