Borderlands 3 Data Processing
=============================

A few utilities I use to extract BL3 data and massage it into a state
that's most useful for data inspection.  I Run BL3 on Linux using
Wine/Proton, so all of these assume Linux as well, so they're probably
not especially useful to most Windows users, alas.

- `link_paks.py`: I like to keep BL3's pakfiles sorted into dirs which
  correspond to the patches in which they were released.  This was easy
  enough to hand-manage when I was just adding them one at a time, as
  patches were released, but when I got the Steam version (in addition
  to EGS) and noticed that some of the checksums of pakfiles didn't
  match, it came time to automate.  Pass it a list of directories in 
  the current dir which start with `pak-`.  Each `pak-*` dir should have a
  `filelist.txt` in it, which is just a list of the pakfiles released
  in that patch.  This util will update symlinks based on a `-s`/`--store`
  argument, and now defaults to Steam.  Optionally, it'll also update
  our checksum files if it's passed `-c`/`--checksum`.  (It'll just
  append to the file.)

  - `checksums-sha256sum-egs.txt`: A list of sha256sum checksums for all
    the pakfiles in BL3, from Epic Games Store.  As of the Steam release,
    these often differ between platforms.

  - `checksums-sha256sum-steam.txt`: A list of sha256sum checksums for all
    the pakfiles in BL3, from Steam.  As of the Steam release, these
    often differ between platforms.

  - Note for both of these that in the patch *after* the Steam release
    (ie: the patch that came with DLC2), five new paks from the previous
    patch got overwritten entirely, so the checksums of five of the paks
    in `pak-2020-03-13-steam_xplay` have been removed, since they'll no
    longer match the live files.

- `unpack_bl3.py`: Written in conjunction with [apple1417](https://github.com/apple1417/).
  Used to call `UnrealPak.exe` (optionally via Wine, on Linux) to
  uncompress a bunch of PAK files and arrange them into a file structure
  which matches their in-game object names.  Will attempt to autodetect
  your BL3 install root, but you can also specify pakfiles/directories
  to unpack manually.  Requires an encryption key to unpack BL3 PAK files;
  you should be able to find that with a quick internet search for
  `borderlands 3 pakfile aes key`.

- `find_dup_packs.py`: Little utility to see if duplicate PAK files
  exist in any dirs.  Just some sanity checks for myself.

- `paksort.py`: Sorts PAK files passed on STDIN "intelligently," rather
  than just alphanumerically (which would otherwise put `pakchunk21`
  inbetween `pakchunk2` and `pakchunk3`, for instance).  Handles the
  patch filename conventions as well, so patches will show up after
  the files they patch.  Basically this can be used to define an order
  of unpacking.

- `objectPropertyGenerator.py`: Written by [FromDarkHell](https://github.com/FromDarkHell/)
  and approved for inclusion in this repo.  This commandline utility
  is used to find attribute names which exist for any given classname
  (which you interactively specify / search for).  It requires the
  presence of files like `UE4Tools_NamesDump.txt` and `UE4Tools_ObjectsDump.txt`,
  which can be generated by most popular UE4/BL3 console unlocker DLLs.
  The files this has been used on is specifically the
  [Universal Unreal Engine 4 Unlocker](https://framedsc.github.io/GeneralGuides/universal_ue4_consoleunlocker.htm)
  but other UE4 console enablers seem to support the same kind of dumped
  output.
  - You will need to alter some file paths near the top of the script, so
    that it can both find those dumpfiles, and know where to write its
    cache.
  - It supports color output on the terminal, using `-c`/`--color` for
    terminals with a black/dark background, or `-w`/`--whitecolor` for
    terminals with a white/light background.  This support requires
    the [colorama Python module](https://pypi.org/project/colorama/) to
    work.  Colorama is not required to actually use the utility, though.

- `bl3-obj-dot.py`: Script to serialize an object file using JohnWickParse,
  generate a [graphviz](https://graphviz.org/) dotfile describing how the
  object exports relate to each other, and convert that to an image (or
  to an SVG, if you configure it that way).  See the program comments for
  specifics.

Processing New Data
-------------------

These are my notes of what I do when a new patch is released.  First,
to prep/extract the data:

1. Create a new `pak-YYYY-MM-DD-note` dir, with a `filelist.txt` inside
   which lists the new/update pakfiles
2. Use `link_paks.py` to symlink the pakfiles into the dir, for the given
   store, and generate updated checksums.  Repeat this for both stores,
   if you want both sets of checksums.
3. Unpack the new `pak-*` dir using `unpack_bl3.py`.  This will leave
   an `extracted_new` dir alongside the main `extracted` dir, with the
   new data.

If you don't care about my `pak-*` directory organization, you can just
lump all the paks in a single dir and `unpack_bl3.py` that dir.

License
-------

All code in this project is is licensed under the
[New/Modified (3-Clause) BSD License](https://opensource.org/licenses/BSD-3-Clause).
A copy can be found in [COPYING.txt](COPYING.txt).

