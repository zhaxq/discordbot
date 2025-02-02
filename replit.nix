{ pkgs }: {
  deps = [
    pkgs.python311  # Asegura que usa Python 3.11
    pkgs.python311Packages.pip
    pkgs.python311Packages.flask  # Para mantener activo el bot
    pkgs.python311Packages.requests
    pkgs.python311Packages.discordpy
  ];
}
