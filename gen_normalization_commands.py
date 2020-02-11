#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:

import os
import io
import re
import sys
import struct

# Script to loop through the current directory and inspect .uasset/.umap files in
# an attempt to find out what the "proper" path is for the UE4 assets, and then
# generate a set of commands which can be used (on Linux, at least) to make the
# on-filesystem paths match the object paths exactly.
#
# This hasn't been run on the "full" set of BL3 assets in quite awhile, and may do
# some things slightly wrong.  There was a bit of weirdness, for instance, with
# the AMD Red Chipper ECHO skin object, which we were briefly (and incorrectly)
# hardcoding to a specific path, though that's been commented since then.
#
# It's been run a few times on "new" patch pak data, though, to put all those in
# place before copying the new data over the previously-extracted dirs, and seems
# to work fine in that context.
#
# Anyway, the code's not especially clean, sorry about that.  Note one more time
# that this just generates commands which you can then run to move the files
# around; it doesn't make any changes itself.

num_re = re.compile('^(.*)_(\d+)$')

def read_int(df):
    return struct.unpack('<i', df.read(4))[0]

def read_str(df):
    strlen = read_int(df)
    if strlen < 0:
        strlen = abs(strlen)
        return df.read(strlen*2)[:-2].decode('utf_16_le')
    else:
        return df.read(strlen)[:-1].decode('latin1')

def get_syms(filename):
    syms = {}
    with open(filename, 'rb') as df:
        # There's a string 28 bytes in, so we can't use entirely absolute positioning.
        # Could be that there's some other strings in here we're unaware of, of course.
        df.seek(28)
        read_str(df)
        # Then there's a bunch of ints we skip (again, maybe some of these are actually
        # zero-length strings?)
        df.seek(80, io.SEEK_CUR)
        num_symbols = read_int(df)
        # Then a bunch more possibly-zero-strengh-length ints
        df.seek(72, io.SEEK_CUR)
        # Now we're ready to actually read our symbols
        for _ in range(num_symbols):
            sym = read_str(df)
            syms[sym.lower()] = sym
            read_int(df)
    return syms

def get_sym_hits(syms, match_str):
    hits = []
    for sym in syms.keys():
        if sym.endswith(match_str):
            hits.append(sym)
    return hits

# Some hardcoded results for edge cases not otherwise worth dealing with
hardcodes = {
        # Oh, huh, this is wrong.  Don't recall what happens without this in here, but
        # that uasset should go into /Game/PlayerCharacters/_Customizations/EchoDevice
        # instead.  Though there *is* an ECHOTheme_35.uasset inside /Game/UI/_Shared
        # too, so eh?
        #'./Game/ECHOTheme_35.uasset': '/Game/UI/_Shared/CustomIconsEcho/ECHOTheme_35',
        }

# TODO: .umap files seem to have locations in there too, and don't have a .uexp of their own.
# So our homedir remains a bit littered with map files which probably shouldn't be there.

cmd_mkdirs = set()
cmd_moves = []
for (dirpath, dirnames, filenames) in os.walk('.'):
    for filename in filenames:
        if filename.endswith('.uasset') or filename.endswith('.umap'):
            is_asset = False
            is_map = False
            if filename.endswith('.uasset'):
                is_asset = True
                base_obj_name = filename[:-7]
            else:
                is_map = True
                base_obj_name = filename[:-5]
            predicted_name = '{}/{}'.format(dirpath[1:], base_obj_name)
            #if dirpath != '.':
            #    predicted_name = '/Game/{}/{}'.format(dirpath[2:], base_obj_name)
            #else:
            #    predicted_name = '/Game/{}'.format(base_obj_name)
            predicted_name_lower = predicted_name.lower()
            full_filename = os.path.join(dirpath, filename)
            actual_result = None
            if full_filename in hardcodes:
                predicted_name = '(hardcoded)'
                actual_result = hardcodes[full_filename]
            else:
                syms = get_syms(full_filename)
                if predicted_name_lower not in syms:
                    # Okay, start chopping off path bits from the front until we find a match
                    found = None
                    found_num = False
                    multiple = False
                    parts = predicted_name_lower.split('/')
                    match = num_re.match(predicted_name_lower)
                    if match:
                        parts_num = match.group(1).split('/')
                        num_suffix = match.group(2)
                    else:
                        parts_num = None
                        num_suffix = None
                    for idx in range(2, len(parts)):
                        to_search = '/{}'.format('/'.join(parts[idx:]))
                        hits = get_sym_hits(syms, to_search)
                        if len(hits) == 1:
                            found = hits[0]
                            break
                        elif len(hits) > 1:
                            multiple = True
                            print('{}: MULTIPLE MATCHES'.format(full_filename))
                            break
                        elif num_suffix is not None:
                            # Check to make sure we don't have a number-suffix fuzzy match.  The most common
                            # occurrence of this is stuff like:
                            # PlayerCharacters/Operative/_Shared/Animation/Rifle/Shotgun/Hyperion/3rd/AS_SG_HYP_Grip_0
                            # where the _0 name seems to often *exist* but the only reference in the file is
                            # without the number.
                            to_search = '/{}'.format('/'.join(parts_num[idx:]))
                            hits = get_sym_hits(syms, to_search)
                            if len(hits) == 1:
                                found = hits[0]
                                found_num = True
                                break
                            elif len(hits) > 1:
                                multiple = True
                                print('{}: MULTIPLE MATCHES (numsuffix)'.format(full_filename))
                                break

                    if found is None:
                        if not multiple:
                            print('{}: NO MATCHES'.format(full_filename))
                    else:
                        if found_num:
                            found_real = '{}_{}'.format(found, num_suffix)
                            actual_result = '{}_{}'.format(syms[found], num_suffix)
                        else:
                            found_real = found
                            actual_result = syms[found]
                        if found_real == predicted_name_lower:
                            actual_result = None

            if actual_result is not None:
                #print('{} | {} -> {}'.format(full_filename, predicted_name, actual_result))
                (dest_dir, dest_result) = os.path.split(actual_result)
                if base_obj_name.lower() != dest_result.lower():
                    raise Exception('{}: base obj name {} does not match result {}'.format(
                        full_filename,
                        base_obj_name,
                        dest_result,
                        ))
                cmd_mkdirs.add(dest_dir)
                if is_asset:
                    cmd_moves.append((full_filename[:-7], dest_dir))
                else:
                    cmd_moves.append((full_filename[:-5], dest_dir))

for mkdir in sorted(cmd_mkdirs):
    print('mkdir -p .{}'.format(mkdir))
for (mv_from, mv_to) in cmd_moves:
    print('mv -i {}.* .{}'.format(mv_from, mv_to))
print('find . -type d -print0 | xargs -0 rmdir -p --ignore-fail-on-non-empty')
