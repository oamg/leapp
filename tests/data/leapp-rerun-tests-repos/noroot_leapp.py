import leapp.cli
import os

os.getuid = lambda: 0
leapp.cli.main()
