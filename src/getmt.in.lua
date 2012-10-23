#!@path_to_lua@/lua
-- -*- lua -*-
-----------------------------------------------------------------
-- getmt:  prints to screen what the value of the ModuleTable is.
--         optionly it writes the state of the ModuleTable is to a
--         dated file.
--
local cmd = arg[0]

local i,j = cmd:find(".*/")
local cmd_dir = "./"
if (i) then
   cmd_dir = cmd:sub(1,j)
end
package.path = cmd_dir .. "?.lua;" .. package.path
require("strict")
require("fileOps")
require("serializeTbl")
require("capture")

_ModuleTable_ = ""
local posix   = require("posix")
local Optiks  = require("Optiks")
local lfs     = require("lfs")
local cmd     = abspath(arg[0])
local i,j     = cmd:find(".*/")
local cmd_dir = "./"
if (i) then
   cmd_dir = cmd:sub(1,j)
end
package.path = cmd_dir .. '?.lua;' .. package.path

local base64       = require("base64")
local concat       = table.concat
local decode64     = base64.decode64
local format       = string.format
local getenv       = os.getenv
local huge         = math.huge

function UUIDString(epoch)
   local ymd  = os.date("*t", epoch)

   --                                y    m    d    h    m    s
   local uuid_date = string.format("%d_%02d_%02d_%02d_%02d_%02d", 
                                   ymd.year, ymd.month, ymd.day, 
                                   ymd.hour, ymd.min,   ymd.sec)
   
   local uuid_str  = capture("uuidgen"):sub(1,-2)
   local uuid      = uuid_date .. "-" .. uuid_str

   return uuid
end

local function epoch()
   if (posix.gettimeofday) then
      local t1, t2 = posix.gettimeofday()
      if (t2 == nil) then
         return t1.sec + t1.usec*1.0e-6
      else
         return t1 + t2*1.0e-6
      end
   else
      return os.time()
   end
end

function getMT()
   local a    = {}
   local mtSz = getenv("_ModuleTable_Sz_") or huge
   local s    = nil

   for i = 1, mtSz do
      local name = format("_ModuleTable%03d_",i)
      local v    = getenv(name)
      if (v == nil) then break end
      a[#a+1]    = v
   end
   if (#a > 0) then
      s = decode64(concat(a,""))
   end
   return s
end

function main()

   local optionTbl = options()

   local s = getMT()
   if (s == nil) then return end

   local t = assert(loadstring(s))()
   local s = serializeTbl{indent=true, name="_ModuleTable_", value=_ModuleTable_}

   local fn = nil
   if (optionTbl.save_state) then
      local uuid = UUIDString(epoch())
      fn = pathJoin(getenv("HOME"), ".lmod.d", ".save", uuid .. ".lua")
   elseif (optionTbl.fn) then
      fn = optionTbl.fn
   end


   if (fn) then
      local d = dirname(fn)
      if (not isDir(d)) then
         mkdir_recursive(d)
      end 

      local f = io.open(fn,"w")
      if (f) then
         f:write(s)
         f:close()
      end
   else
      print (s)
   end
end

function options()
   local usage         = "Usage: getmt [options]"
   local cmdlineParser = Optiks:new{usage=usage, version="1.0"}

   cmdlineParser:add_option{ 
      name   = {'-v','--verbose'},
      dest   = 'verbosityLevel',
      action = 'count',
   }

   cmdlineParser:add_option{ 
      name   = {'-f', '--file'},
      dest   = 'fn',
      action = 'store',
   }

   cmdlineParser:add_option{ 
      name   = {'-s', '--save_state'},
      dest   = 'save_state',
      action = 'store_true',
   }

   local optionTbl, pargs = cmdlineParser:parse(arg)

   return optionTbl

end
main()