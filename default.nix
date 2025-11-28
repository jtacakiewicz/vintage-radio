with import <nixpkgs> {};

let 
    python = pkgs.python310;
    pythonPackages = python.pkgs;
    lib-path = with pkgs; lib.makeLibraryPath [
        libffi
        openssl
        stdenv.cc.cc
    ];
    pyPkgs = with pythonPackages; [
        venvShellHook
        uv
    ];
in pkgs.mkShell {
    name = "python-env";
    packages = [
        arduino-cli
        micronucleus
        python
        pyPkgs
    ];
    buildInputs = with pkgs; [
        python313Packages.python-lsp-server
        pandoc
        texliveTeTeX
        openssl
        git
        openssh
        rsync
        glib
        zlib
        libGL
        fontconfig
        xorg.libX11
        libxkbcommon
        freetype
        dbus
    ];
    shellHook = ''
        export "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${lib-path}"
        VENV=.venv

        if test ! -d $VENV; then
            uv venv
            echo "if you want to use other python version use 'export UV_PYTHON=3.x' and remove current .venv"
        fi
        source ./$VENV/bin/activate
        source .env
        if [ -f requirements.txt ]; then
            uv pip install -r requirements.txt
        fi
        if command -v zsh >/dev/null 2>&1

        arduino-cli core install digistump:avr

        then
            exec zsh
        fi
    '';

    postShellHook = ''
        ln -sf ${python.sitePackages}/* ./.venv/lib/python/site-packages
    '';
}
