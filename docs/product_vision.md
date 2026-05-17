# Nexa AI — Product Vision

## 1. Product Summary

Nexa AI is a futuristic Windows desktop personal voice assistant designed to make everyday computer use faster, more natural, and more intelligent. It combines a cyberpunk/Jarvis-style Electron + React desktop interface with a Python FastAPI automation backend to support Bengali, English, and mixed-language voice commands for desktop control, information retrieval, productivity, and study support.

The product is intended to feel advanced to users while remaining practical to build, maintain, and run on low-end Windows laptops. Its architecture should be modular, beginner-friendly for contributors, and production-oriented from the beginning.

## 2. Target Users

- Students who want reminders, study help, document assistance, and quick information access
- Everyday Windows users who want hands-free desktop automation
- Bengali-speaking users who naturally mix Bengali and English while giving commands
- Productivity-focused users who want faster access to apps, websites, files, drafts, and web information
- Beginner developers who want to understand and extend a real-world assistant system without sacrificing good architecture

## 3. Core Problems Solved

Nexa AI should reduce the friction of using a computer by solving these problems:

- Repetitive manual actions take too many clicks
- Many assistants do not understand Bengali-English mixed commands well
- Users often forget reminders, study tasks, and follow-ups
- Finding files, opening tools, and organizing work can be slow
- Drafting messages and emails from scratch takes time
- Useful desktop assistants often depend on paid APIs or hardware too demanding for low-end laptops
- Beginner-friendly projects are often not structured well enough for real production growth

## 4. Main Features

- Futuristic Windows desktop interface with Electron + React
- Python FastAPI automation backend
- Bengali, English, and mixed-language command understanding
- Typo-tolerant and variation-tolerant command interpretation
- Voice-based desktop automation
- App and website launcher
- Browser and YouTube control
- File search and lightweight organization tools
- WhatsApp and email draft assistance
- Reminders and study assistant features
- PDF and document assistance
- Web, news, weather, and dictionary intelligence using free/public internet sources
- Local SQLite-based memory for preferences, reminders, and assistant state
- Security and permission controls for sensitive actions
- Modular structure that allows future expansion without rewriting the system

## 5. Free / No-Paid-API Policy

Nexa AI will avoid paid APIs as a core product rule.

- Core functionality must not depend on subscription-only services
- Internet-based features should use free, public, or open sources whenever available
- The assistant should remain useful even when internet access is unavailable
- If optional external integrations are added later, they must not make the main product unusable without payment

This policy keeps Nexa AI accessible, sustainable, and aligned with users who need capable software without recurring cost.

## 6. Lightweight Performance Goal

Nexa AI must be usable on low-end Windows laptops.

- Keep background CPU and memory usage modest
- Prefer lightweight local components where practical
- Avoid unnecessary always-on heavy processing
- Use SQLite for simple local persistence
- Load features modularly so inactive capabilities do not consume resources
- Design the UI to feel responsive even on weaker hardware

The goal is not only to look futuristic, but to behave efficiently enough for everyday real-world machines.

## 7. Production Release Goal

Nexa AI should be developed as a real product, not only a prototype.

Production readiness means:

- Modular, maintainable architecture
- Clear separation between desktop UI, automation services, command understanding, integrations, and storage
- Secure permission handling for sensitive actions
- Graceful error handling and useful logs
- Stable behavior across common Windows environments
- Beginner-friendly code organization with room for professional scaling
- Documentation that supports onboarding, testing, maintenance, and future contributors

The intended release path is a dependable Windows assistant that can be installed, updated, and trusted by real users.

## 8. Future Smart Home Vision

In later phases, Nexa AI should expand beyond the desktop into smart home control through ESP32-based devices.

Possible future capabilities include:

- Voice-controlled lights, fans, and room devices
- Local-network communication with ESP32 modules
- Custom low-cost smart home workflows
- Unified control of desktop productivity and physical environment from one assistant

This future direction should influence the architecture now: the system should be extensible enough to add device modules later without disturbing the desktop core.

## 9. High-Level System Vision

Nexa AI should be organized as a set of clear, cooperating modules:

1. **Desktop Experience Layer**  
   Electron + React UI for voice interaction, status display, notifications, and settings.

2. **Automation Service Layer**  
   Python FastAPI backend responsible for executing safe desktop actions, routing tasks, and exposing local APIs to the desktop app.

3. **Command Understanding Layer**  
   Bengali-English mixed command parsing with typo tolerance, aliases, fuzzy matching, and intent detection.

4. **Capability Modules**  
   Independent modules for launching apps, browser control, files, reminders, study help, drafts, documents, and web intelligence.

5. **Local Memory Layer**  
   SQLite storage for reminders, preferences, history, permissions, and lightweight persistent context.

6. **Security and Permission Layer**  
   Rules for confirming, restricting, logging, or blocking sensitive actions.

7. **External Intelligence Layer**  
   Free/public internet sources for weather, news, dictionary, and web lookup when online information is required.

This structure should let Nexa AI grow feature by feature while keeping each part understandable and replaceable.

## 10. What Will Be Included in the MVP

The first production-oriented MVP should include:

- Windows desktop assistant shell with cyberpunk/Jarvis-inspired UI
- Voice input and response flow
- Bengali, English, and mixed-language basic command handling
- Typo-tolerant command matching for common actions
- App launcher
- Website launcher
- Basic browser and YouTube control
- File search
- Reminder creation and retrieval
- Basic study assistant utilities
- PDF/document question and summary support at a practical MVP level
- WhatsApp/email draft generation assistance
- Free-source web, weather, news, and dictionary lookup
- Local SQLite memory
- Security and permission foundation for sensitive commands
- Modular project architecture and documentation

## 11. What Will Be Added Later

Later releases may add:

- More advanced natural-language understanding
- Richer Bengali language support and command personalization
- Deeper file organization and workflow automation
- More capable email and messaging integrations
- Stronger study planning, revision, and productivity coaching
- Expanded document intelligence
- Offline intelligence improvements where feasible
- Plugin-style extension system
- User profiles and richer personalization
- Advanced permission management and audit history
- ESP32 smart home device control
- Multi-device ecosystem features

Nexa AI should begin with a focused, reliable desktop core and then expand outward only when the foundation is strong.
