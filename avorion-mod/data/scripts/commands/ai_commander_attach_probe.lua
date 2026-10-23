-- Source-only M1 command candidate.
-- Automatic command discovery from a mod and mod-relative script resolution
-- have not been verified in the installed Avorion build.

local PROBE_SCRIPT_PATH = "data/scripts/entity/ai_commander_probe.lua"
-- Keep empty until a disposable test target has been created and its ID verified.
-- An empty value makes this command fail closed.
local ALLOWED_TARGET_ID = ""

local function inspectString(readValue)
    local ok, value = pcall(readValue)
    if not ok or value == nil then
        return "unavailable"
    end

    local stringOk, stringValue = pcall(tostring, value)
    if not stringOk then
        return "unavailable"
    end

    return stringValue
end

function execute(playerIndex, commandName, ...)
    local argumentCount = select("#", ...)
    local inspectMode = argumentCount == 1 and select(1, ...) == "inspect"
    if argumentCount ~= 0 and not inspectMode then
        return 1, "", "Usage: /ai_commander_attach_probe inspect or /ai_commander_attach_probe"
    end

    if playerIndex == nil then
        return 1, "", "This command requires an in-game player; console and RCON calls are rejected."
    end

    local player = Player(playerIndex)
    if not valid(player) then
        return 1, "", "The in-game player could not be resolved."
    end

    if not Server():hasAdminPrivileges(player) then
        return 1, "", "Admin privileges are required."
    end

    if not inspectMode and select("#", ...) ~= 0 then
        return 1, "", "This command accepts no arguments; select the target ship in game."
    end

    local craft = player.craft
    if not valid(craft) then
        return 1, "", "The player must be aboard a ship."
    end

    local target = craft.selectedObject
    if not valid(target) then
        return 1, "", "No valid selected target was found."
    end

    if not target.isShip then
        return 1, "", "The selected target is not a ship."
    end

    local owner = Owner(target)
    if not valid(owner) or not owner.isAIFaction then
        return 1, "", "The selected ship is not owned by an AI faction."
    end

    if inspectMode then
        local targetId = inspectString(function() return target.id.string end)
        local serverFolder = inspectString(function() return Server().folder end)
        local message = "Inspect: ship_id=" .. targetId
            .. "; server_folder=" .. serverFolder
            .. "; AI-owner=true"
            .. "; probe_script_path=" .. PROBE_SCRIPT_PATH
        return 0, message, ""
    end

    if ALLOWED_TARGET_ID == "" then
        return 1, "", "No disposable test ship is allowlisted; no attach was requested."
    end

    if target.id.string ~= ALLOWED_TARGET_ID then
        return 1, "", "The selected ship is not the allowlisted test target."
    end

    -- Point-in-time duplicate check. API docs do not establish atomic exactly-once
    -- behavior, and the mod-relative path mapping remains a candidate.
    if target:hasScript(PROBE_SCRIPT_PATH) then
        return 0, "Probe already appears attached; no new attach was requested.", ""
    end

    target:addScriptOnce(PROBE_SCRIPT_PATH)
    return 0, "Attach requested for the selected ship; runtime attachment is unconfirmed.", ""
end

function getDescription()
    return "Requests the passive AI Commander probe on the selected ship."
end

function getHelp()
    return "Usage:\n  /ai_commander_attach_probe inspect (read-only preflight)\n  /ai_commander_attach_probe (attach request; select a ship first)"
end
