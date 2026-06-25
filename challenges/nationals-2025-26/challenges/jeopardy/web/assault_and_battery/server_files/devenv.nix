{
  pkgs,
  config,
  ...
}: let
  appName = "reclaimer_central";

  ports = {
    app = 8000;
    opensearch = 9200;
  };

  projectPath = dir: "${config.devenv.root}/${dir}";
in {
  name = "Assault and Battery";

  imports = [
    ./devenv
  ];

  infoSections = {
    authors = [
      "Robert Babaev"
    ];
  };

  env = let
    procs = config.processes;
    apiPort = procs.app.ports.http.value;
    opensearchPort = procs.opensearch.ports.http.value;
  in {
    APP_NAME = appName;
    APP_PORT = apiPort;
    OPENSEARCH_PORT = opensearchPort;
    OPENSEARCH_URL = "http://localhost:${toString opensearchPort}";
  };

  packages = with pkgs; [
    git
  ];

  cachix.pull = ["rbabaev"];

  scripts = {
    run-tests = {
      exec = ''
        devenv processes up opensearch -d
        uv run pytest --nf --lf
        devenv processes down
      '';
    };
    init-db = {
      exec = ''
        cd ${projectPath ""}
        devenv processes up opensearch -d
        uv run manage.py migrate
        uv run manage.py loaddata ${projectPath "scripts/data/fixtures.json"}
        devenv processes down
      '';
    };
    run-bot = {
      exec = ''
        uv run ${projectPath "scripts/bot.py"}
      '';
    };
    mkrelease = {
      exec = ''
        cd ${projectPath ""}
        uv run ${projectPath "scripts/pack.py"}
        scp ${projectPath "server.tar.xz"} assault-and-battery:~
      '';
    };
  };

  services.opensearch = {
    settings = {
      "http.port" = ports.opensearch;
    };
  };
  processes = {
    app = {
      ports = {
        http.allocate = ports.app;
      };
      exec = let
        bindAddr = "0.0.0.0:${toString ports.app}";
      in ''
        uv run gunicorn ${appName}.wsgi --workers 4 --timeout 60 --bind ${bindAddr}
      '';
      cwd = config.devenv.root;
      after = ["devenv:processes:opensearch@ready"];
      ready = {
        http.get = {
          port = ports.app;
          path = "/api/system/health/";
        };
      };
    };

    bot = {
      exec = ''
        uv run ${projectPath "scripts/bot.py"}
      '';
      cwd = config.devenv.root;
      after = ["devenv:processes:app"];
    };
  };

  languages = {
    python = {
      enable = true;
      uv = {
        enable = true;
      };
    };
  };

  difftastic.enable = true;
}
