{
  pkgs,
  lib,
  config,
  ...
}: let
  shellnet = config.languages.rust.import ./shellnet {};
  telnetd = {
    port = 2333;
    bind = "0.0.0.0";
    binary = "${pkgs.inetutils}/libexec/telnetd";
  };
in {
  # https://devenv.sh/packages/
  packages = with pkgs; [
    git
    inetutils
    socat
    shellnet
  ];

  languages = {
    rust = {
      enable = true;
    };
  };

  processes = {
    proxy = with telnetd; {
      exec = ''
        sudo ${lib.getExe pkgs.socat} \
          TCP-LISTEN:${builtins.toString port},bind=${bind},reuseaddr,fork \
          EXEC:"${binary} -E ${lib.getExe shellnet}"
      '';
    };
  };

  scripts = {
    mkrelease = {
      exec = ''
        cd ${config.devenv.root}/shellnet
        cargo build --release
        cp target/release/shellnet ${config.devenv.root}/../release_files
        cd ${config.devenv.root}
        ${lib.getExe pkgs.git} archive --format tar.gz HEAD . > server.tar.gz
      '';
    };
  };
}
