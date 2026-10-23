-- Local source template. Metadata field names follow installed modinfo.lua examples;
-- compatibility and automatic loading have not been validated in Avorion 2.5.13.
meta =
{
    id = "local_avorion_ai_commander",
    name = "Avorion AI Commander Probe",
    title = "Avorion AI Commander Probe",
    type = "mod",
    description = "Passive M1 probe source template. No ship actions are issued.",
    authors = {"Avorion AI Commander project"},
    version = "0.1.0",
    serverSideOnly = true,
    clientSideOnly = false,
    -- Attaching an entity script may persist on a save; test only on an approved
    -- disposable galaxy after the isolation gates are closed.
    saveGameAltering = true,
}
