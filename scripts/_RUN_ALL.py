if __name__ == "__main__":
    import sys
    from subprocess import check_call

    scripts = [
        "01_normalize_packages.py",
        "02_extra_downloads.py",
        "03_build_icon_resource.py",
        "04_build_rc.py",
        "05_build_ui.py",
    ]

    for script in scripts:
        if script.endswith(".py"):
            check_call([sys.executable, script])
        else:
            check_call(script)
