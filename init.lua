--
-- formspec_ast: An abstract system tree for formspecs.
--
-- This does not actually depend on Minetest and could probably run in
-- standalone Lua.
--
-- The MIT License (MIT)
--
-- Copyright © 2019 by luk3yx.
--
-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to
-- deal in the Software without restriction, including without limitation the
-- rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
-- sell copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:
--
-- The above copyright notice and this permission notice shall be included in
-- all copies or substantial portions of the Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
-- FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
-- IN THE SOFTWARE.
--

formspec_ast = {}

local minetest = minetest
local modpath

if minetest then
    -- Running inside Minetest.
    modpath = minetest.get_modpath('formspec_ast')
    is_yes = minetest.is_yes
    assert(minetest.get_current_modname() == 'formspec_ast',
           'This mod must be called formspec_ast!')
else
    -- Probably running outside Minetest.
    modpath = '.'
    minetest = core or {}
    function minetest.is_yes(str)
        str = str:lower()
        return str == 'true' or str == 'yes'
    end
    function string.trim(str)
        return str:gsub("^%s*(.-)%s*$", "%1")
    end
end

formspec_ast.modpath, formspec_ast.minetest = modpath, minetest

dofile(modpath .. '/core.lua')
dofile(modpath .. '/helpers.lua')
dofile(modpath .. '/safety.lua')

formspec_ast.modpath, formspec_ast.minetest = nil, nil
