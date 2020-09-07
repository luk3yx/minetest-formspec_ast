-- dofile('init.lua')
dofile('test.lua')

local function equal(t1, t2)
    if type(t1) ~= 'table' or type(t2) ~= 'table' then
        return t1 == t2
    end
    for k, v in pairs(t1) do
        if not equal(v, t2[k]) then
            print(k, v, dump(t1), dump(t2))
            return false
        end
    end
    for k, v in pairs(t2) do
        if t1[k] == nil then
            return false
        end
    end
    return true
end

local function assert_equal(obj1, ...)
    for i = 1, select('#', ...) do
        objn = select(i, ...)
        if not equal(obj1, objn) then
            error(('%s ~= %s'):format(obj1, objn))
        end
    end
end

local function test_parse(fs, expected_tree)
    -- Make single elements lists and add formspec_version
    if expected_tree.type then
        expected_tree = {expected_tree}
    end
    if not expected_tree.formspec_version then
        expected_tree.formspec_version = 1
    end

    local tree = assert(formspec_ast.parse(fs))
    assert_equal(tree, expected_tree)
end

local function test_parse_unparse(fs, expected_tree)
    test_parse(fs, expected_tree)
    local unparsed_fs = assert(formspec_ast.unparse(expected_tree))
    assert_equal(fs, unparsed_fs)
end

local fs = [[
    formspec_version[2]
    size[5,2]
    container[1,1]
        label[0,0;Containers are fun]
        container[-1,-1]
            button[0.5,0;4,1;name;Label]
        container_end[]
        label[0,1;Nested containers work too.]
        scroll_container[0,2;1,1;scrollbar;vertical]
            button[0.5,0;4,1;name;Label]
        scroll_container_end[]
    container_end[]
    image[0,1;1,1;air.png]
    set_focus[name;true]
]]
fs = ('\n' .. fs):gsub('\n[ \n]*', '')

test_parse_unparse(fs, {
    formspec_version = 2,
    {
        type = "size",
        w = 5,
        h = 2,
    },
    {
        type = "container",
        x = 1,
        y = 1,
        {
            type = "label",
            x = 0,
            y = 0,
            label = "Containers are fun",
        },
        {
            type = "container",
            x = -1,
            y = -1,
            {
                type = "button",
                x = 0.5,
                y = 0,
                w = 4,
                h = 1,
                name = "name",
                label = "Label",
            },
        },
        {
            type = "label",
            x = 0,
            y = 1,
            label = "Nested containers work too.",
        },
        {
            type = "scroll_container",
            x = 0,
            y = 2,
            w = 1,
            h = 1,
            scrollbar_name = "scrollbar",
            orientation = "vertical",
            -- scroll_factor = nil,
            {
                h = 1,
                y = 0,
                label = "Label",
                w = 4,
                name = "name",
                x = 0.5,
                type = "button"
            },
        },
    },
    {
        type = "image",
        x = 0,
        y = 1,
        w = 1,
        h = 1,
        texture_name = "air.png",
    },
    {
        type = "set_focus",
        name = "name",
        force = true,
    }
})


-- Make sure style[] (un)parses correctly
local s = 'style[test1,test2;def=ghi]style_type[test;abc=def]'
assert_equal(s, assert(formspec_ast.interpret(s)))
test_parse('style[name,name2;bgcolor=blue;textcolor=yellow]', {
    type = "style",
    selectors = {
        "name",
        "name2",
    },
    props = {
        bgcolor = "blue",
        textcolor = "yellow",
    },
})

-- Ensure the style[] unparse compatibility works correctly
assert_equal(
    'style_type[test;abc=def]',
    assert(formspec_ast.unparse({
        {
            type = 'style_type',
            name = 'test',
            props = {
                abc = 'def',
            },
        }
    })),
    assert(formspec_ast.unparse({
        {
            type = 'style_type',
            selectors = {
                'test',
            },
            props = {
                abc = 'def',
            },
        }
    }))
)

print('Tests pass')
