-- Passive M1 source template only.
-- No ShipAI calls, commands, targets, or world mutations are implemented here.
-- The script is not auto-attached: the loading/attachment point for this project
-- has not been established. Attach only in a separately approved test setup.
--
-- All file/path behavior, the Server().folder + moddata path, append/tail behavior,
-- Uuid tostring format, translationf component access, and number serialization
-- remain unvalidated at runtime. The one-second cadence is a provisional proposal.

-- Don't remove this comment; it identifies the namespace pattern used by Avorion scripts.
-- namespace AICommanderProbe
AICommanderProbe = {}

local protocolVersion = "1"
local maximumRecordBytes = 512
local maximumRecordsPerDirection = 106 -- HELLO + 50 cycles + up to 5 negative cases
local maximumProbes = 50
local maximumNegativeRecords = 5
local maximumLogBytes = 64 * 1024
local activeSession = nil
local lastProbeSequence = 0
local lastAckSequence = 0
local inboxLineCount = 0
local outboxLineCount = 0
local outboxBytes = 0
local negativeInputCount = 0
local errorOutputCount = 0
local inboxPath = nil
local outboxPath = nil
local channelReady = false
local appendRecord

local function failClosed(reason)
    channelReady = false
    activeSession = nil
    print("[AICommanderProbe] Probe channel disabled: " .. reason)
end

local function rejectInput(reason)
    negativeInputCount = negativeInputCount + 1
    if negativeInputCount > maximumNegativeRecords then
        failClosed("negative-record limit exceeded")
        return
    end

    if activeSession then
        appendRecord("ERROR", activeSession, 0, reason)
    end
end

local function splitRecord(line)
    local fields = {}
    local startAt = 1

    while true do
        local separatorAt = line:find("|", startAt, true)
        if not separatorAt then
            fields[#fields + 1] = line:sub(startAt)
            break
        end

        fields[#fields + 1] = line:sub(startAt, separatorAt - 1)
        startAt = separatorAt + 1
    end

    return fields
end

local function isSessionId(value)
    return type(value) == "string" and #value == 32 and value:match("^[0-9a-f]+$") ~= nil
end

local function parseSequence(value)
    if type(value) ~= "string" or not value:match("^%d+$") then
        return nil
    end

    local sequence = tonumber(value)
    if not sequence or sequence < 1 or sequence > 2147483647 or sequence % 1 ~= 0 then
        return nil
    end

    return sequence
end

appendRecord = function(recordType, ...)
    if not outboxPath or not channelReady then
        return false
    end

    if outboxLineCount >= maximumRecordsPerDirection then
        failClosed("outbox record limit reached")
        return false
    end
    if recordType == "ERROR" and errorOutputCount >= maximumNegativeRecords then
        failClosed("error-record limit reached")
        return false
    end

    local fields = {"AC", protocolVersion, recordType}
    local values = {...}
    for _, value in ipairs(values) do
        local field = tostring(value)
        if field:find("|", 1, true) or field:find("\n", 1, true)
            or field:find("\r", 1, true) or field:find(string.char(0), 1, true) then
            return false
        end
        fields[#fields + 1] = field
    end

    local record = table.concat(fields, "|") .. "\n"
    if #record > maximumRecordBytes then
        return false
    end
    if outboxBytes + #record > maximumLogBytes then
        failClosed("outbox byte limit reached")
        return false
    end

    local file, openError = io.open(outboxPath, "a")
    if not file then
        failClosed("outbox open failed: " .. tostring(openError))
        return false
    end

    local writeResult, writeError = file:write(record)
    if not writeResult then
        -- Disable first; close below is only handle cleanup and never retries a record.
        failClosed("outbox write failed: " .. tostring(writeError))
    end

    local closeResult, closeError = file:close()
    if not closeResult then
        failClosed("outbox close failed: " .. tostring(closeError))
    end
    if not writeResult or not closeResult then
        return false
    end

    outboxLineCount = outboxLineCount + 1
    outboxBytes = outboxBytes + #record
    if recordType == "ERROR" then
        errorOutputCount = errorOutputCount + 1
    end
    return true
end

local function encodeNumber(value)
    if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then
        return nil
    end

    -- The decimal separator replacement is provisional; locale behavior is untested.
    local encoded = string.format("%.9f", value):gsub(",", ".")
    return encoded
end

local function appendState(sequence)
    local ship = Entity()
    if not valid(ship) then
        appendRecord("ERROR", activeSession, sequence, "invalid_entity")
        return false
    end

    local translation = ship.translationf
    if not translation then
        appendRecord("ERROR", activeSession, sequence, "state_unavailable")
        return false
    end

    local nonnegativeValues = {
        ship.durability,
        ship.maxDurability,
        ship.shieldDurability,
        ship.shieldMaxDurability,
    }
    for index = 1, 4 do
        local value = nonnegativeValues[index]
        if type(value) ~= "number" or value < 0 or value ~= value
            or value == math.huge or value == -math.huge then
            appendRecord("ERROR", activeSession, sequence, "state_unavailable")
            return false
        end
    end

    -- Entity.id.string is documented; its format and wire round-trip remain unverified.
    -- translationf is documented as vec3; numeric x/y/z access is not runtime-tested.
    local entityId = ship.id
    local shipId = entityId and entityId.string
    if type(shipId) ~= "string" or #shipId < 1 or #shipId > 128 then
        appendRecord("ERROR", activeSession, sequence, "state_unavailable")
        return false
    end
    for index = 1, #shipId do
        local byte = string.byte(shipId, index)
        if byte < 0x21 or byte > 0x7E or byte == 0x7C then
            appendRecord("ERROR", activeSession, sequence, "state_unavailable")
            return false
        end
    end

    local values = {
        encodeNumber(ship.durability),
        encodeNumber(ship.maxDurability),
        encodeNumber(ship.shieldDurability),
        encodeNumber(ship.shieldMaxDurability),
        ship.isShieldActive and "1" or "0",
        encodeNumber(translation.x),
        encodeNumber(translation.y),
        encodeNumber(translation.z),
    }

    for index = 1, 8 do
        if values[index] == nil then
            appendRecord("ERROR", activeSession, sequence, "state_unavailable")
            return false
        end
    end

    return appendRecord("STATE", activeSession, sequence, shipId,
        values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8])
end

local function processRecord(line)
    if #line == 0 or #line + 1 > maximumRecordBytes
        or line:find("\r", 1, true) or line:find(string.char(0), 1, true) then
        rejectInput("malformed_record")
        return
    end

    local fields = splitRecord(line)
    if fields[1] ~= "AC" or fields[2] ~= protocolVersion or not fields[3] then
        rejectInput("malformed_record")
        return
    end

    local recordType = fields[3]
    if recordType == "HELLO" then
        if #fields ~= 4 or not isSessionId(fields[4]) then
            rejectInput("invalid_session")
            return
        end
        if activeSession then
            rejectInput("invalid_session")
            return
        end

        activeSession = fields[4]
        lastProbeSequence = 0
        lastAckSequence = 0
        appendRecord("HELLO_ACK", activeSession)
        return
    end

    if recordType == "PROBE" then
        if #fields ~= 5 then
            rejectInput("malformed_record")
            return
        end
        if not activeSession or fields[4] ~= activeSession then
            rejectInput("invalid_session")
            return
        end

        local sequence = parseSequence(fields[5])
        -- AC|1 is stop-and-wait: do not accept the next PROBE before the prior ACK.
        if lastProbeSequence ~= lastAckSequence or not sequence
            or sequence > maximumProbes or sequence ~= lastProbeSequence + 1 then
            appendRecord("ERROR", activeSession, sequence or 0, "unexpected_sequence")
            negativeInputCount = negativeInputCount + 1
            if negativeInputCount > maximumNegativeRecords then
                failClosed("negative-record limit exceeded")
            end
            return
        end

        if appendState(sequence) then
            lastProbeSequence = sequence
        end
        return
    end

    if recordType == "ACK" then
        if #fields ~= 5 then
            rejectInput("malformed_record")
            return
        end
        if not activeSession or fields[4] ~= activeSession then
            rejectInput("invalid_session")
            return
        end

        local sequence = parseSequence(fields[5])
        if not sequence or sequence ~= lastProbeSequence or sequence <= lastAckSequence then
            appendRecord("ERROR", activeSession, sequence or 0, "unexpected_sequence")
            negativeInputCount = negativeInputCount + 1
            if negativeInputCount > maximumNegativeRecords then
                failClosed("negative-record limit exceeded")
            end
            return
        end

        if appendRecord("ACKED", activeSession, sequence) then
            lastAckSequence = sequence
        end
        return
    end

    rejectInput("unknown_type")
end

local function absentOrEmpty(path)
    local file = io.open(path, "r")
    if not file then
        return true
    end
    local firstByte = file:read(1)
    file:close()
    return firstByte == nil
end

if onServer() then

function AICommanderProbe.getUpdateInterval()
    return 1.0
end

function AICommanderProbe.initialize()
    local server = Server()
    -- This path is a research candidate only; directory creation and actual resolution
    -- have not been proven. The script deliberately does not create or modify directories.
    local dataDirectory = server.folder .. "/moddata/avorion-ai-commander"
    inboxPath = dataDirectory .. "/bridge-to-mod.log"
    outboxPath = dataDirectory .. "/mod-to-bridge.log"
    inboxLineCount = 0
    outboxLineCount = 0
    outboxBytes = 0
    negativeInputCount = 0
    errorOutputCount = 0
    activeSession = nil
    lastProbeSequence = 0
    lastAckSequence = 0
    channelReady = absentOrEmpty(inboxPath) and absentOrEmpty(outboxPath)
    if not channelReady then
        failClosed("channel files are not fresh and empty; use a new isolated test directory")
    end
end

function AICommanderProbe.updateServer(timeStep)
    if not inboxPath or not channelReady then
        return
    end

    local file = io.open(inboxPath, "r")
    if not file then
        return
    end

    -- Bounded read: io.read(n) is standard Lua behavior but still needs game-sandbox validation.
    local contents = file:read(maximumLogBytes + 1)
    file:close()
    if type(contents) ~= "string" then
        return
    end
    if #contents > maximumLogBytes then
        failClosed("inbox byte limit reached")
        return
    end

    -- Only process LF-terminated records. An incomplete tail is retried on the next update.
    local lineCount = 0
    local startAt = 1
    while true do
        local newlineAt = contents:find("\n", startAt, true)
        if not newlineAt then
            break
        end

        lineCount = lineCount + 1
        if lineCount > maximumRecordsPerDirection then
            failClosed("inbox record limit reached")
            return
        end
        if lineCount > inboxLineCount then
            local line = contents:sub(startAt, newlineAt - 1)
            processRecord(line)
            if not channelReady then
                return
            end
        end
        startAt = newlineAt + 1
    end

    inboxLineCount = lineCount
end

end
