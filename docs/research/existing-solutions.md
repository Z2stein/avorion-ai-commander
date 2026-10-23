# Existing solutions: AI, combat, and bridges

This is a design-oriented index of public projects, not a report of mods installed on any particular machine. The linked descriptions have not been refreshed for this export; current availability, compatibility, and licensing must be checked before use. No code is adopted by this project.

## Design themes

- Defensive automation can be organized around explicit triggers, a small reaction set, saved/restored order queues, and deterministic fallback.
- Combat AI can use bounded target scoring and hysteresis rather than asking an LLM to select arbitrary entities or issue direct game calls.
- Fleet command tools illustrate group scope, explicit commands, status feedback, and the limits of sector-local information.
- Voice or event-driven assistants can provide situational feedback without being an autonomous tactical commander.
- A game-mod plus external-process bridge is an architectural analogy only. Its APIs and safety properties do not transfer automatically to Avorion.

## Public references

| Project | Publicly described focus | Use in this project |
|---|---|---|
| [Xavorion: Combat AI](https://steamcommunity.com/sharedfiles/filedetails/?id=2992808971) | Combat behaviors, target selection, and equipment-aware NPC behavior. | Concept reference only. Compatibility, dependencies, and code license are not established here. |
| [FleetControl](https://github.com/w00zla/avorion-fleetcontrol) | Fleet groups, commands, and status UI. | UI and command-scope concepts only. Check maintenance, compatibility, and license before reuse. |
| [Fleet Command](https://steamcommunity.com/sharedfiles/filedetails/?id=3723186924) | Fleet roles, formations, escort/guard, and routing concepts. | Feature reference only. Check availability, restrictions, compatibility, and license before use. |
| [VI assistant](https://steamcommunity.com/sharedfiles/filedetails/?id=3580966892) | Event-triggered voice feedback and simple assistance. | Situational-awareness concept; not evidence of an LLM commander. |
| [CaptainMyShip](https://github.com/lethargi/CaptainMyShip) | A project for issuing ship commands. | Inspect its current state and license before treating it as a dependency or code source. |
| [Factorio AI Player v3](https://github.com/thedemon117/ai-player-v3) | A different game's mod/bridge pattern with external decision-making. | Cross-game architecture analogy only; it is not Avorion API or sandbox evidence. |
| [Avorion Announcer](https://steamcommunity.com/sharedfiles/filedetails/?id=2032319866) | A community integration described as using Python and RCON. | RCON integration example only; compatibility with the target build is unverified. |

## Reuse and compatibility limits

Public descriptions establish only what their authors claim. They do not prove that a project is available, compatible with the target Avorion version, safe to install, or licensed for code reuse. Review each source's current license and dependencies separately. Prefer design principles over copying code until those checks pass.

For this proof of concept, useful principles are explicit triggers, a bounded action list, deterministic validation, preserving existing orders, safe fallback, and observable results. This project does not depend on any listed mod.
