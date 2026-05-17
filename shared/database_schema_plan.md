# Nexa AI — Database Schema Plan

This document records the planned SQLite tables for Nexa AI before implementation begins.

| Table | Purpose | Important Fields | Module Owner | Priority |
|---|---|---|---|---|
| `user_profile` | Store core user identity and addressing preferences | `id`, `display_name`, `address_style`, `preferred_language`, `created_at`, `updated_at` | Onboarding & Profile | MVP |
| `user_preferences` | Store configurable assistant preferences | `id`, `user_id`, `key`, `value`, `updated_at` | Memory & Personalization | MVP |
| `command_aliases` | Store aliases and phrase variations for commands | `id`, `intent_name`, `alias_text`, `language_tag`, `active` | Command Understanding | MVP |
| `intent_examples` | Store example utterances for intents | `id`, `intent_name`, `example_text`, `language_tag` | Command Understanding | MVP |
| `interaction_logs` | Record user interactions and outcomes | `id`, `input_text`, `intent_name`, `status`, `created_at` | Shared / Analytics | MVP |
| `conversation_sessions` | Group conversational interactions | `id`, `started_at`, `ended_at`, `title` | AI Chat & Conversation | V2 |
| `conversation_messages` | Store individual chat messages | `id`, `session_id`, `role`, `content`, `created_at` | AI Chat & Conversation | V2 |
| `app_shortcuts` | Store known apps and launch metadata | `id`, `display_name`, `executable_path`, `aliases`, `active` | App & Website Launcher | MVP |
| `website_shortcuts` | Store saved websites and aliases | `id`, `display_name`, `url`, `aliases`, `active` | App & Website Launcher | MVP |
| `contacts` | Store local contact records | `id`, `display_name`, `phone`, `email`, `notes` | Contacts & Drafts | MVP |
| `message_drafts` | Store generated message/email drafts | `id`, `channel`, `recipient_id`, `subject`, `body`, `created_at` | Contacts & Drafts | MVP |
| `reminders` | Store reminder definitions and lifecycle state | `id`, `title`, `due_at`, `status`, `created_at` | Reminder Assistant | MVP |
| `tasks` | Store task items and completion state | `id`, `title`, `due_at`, `priority`, `status` | Reminder & Study Assistant | MVP |
| `file_index` | Store searchable file metadata | `id`, `path`, `name`, `extension`, `size_bytes`, `modified_at` | File Search & Organizer | MVP |
| `file_action_history` | Record confirmed file operations | `id`, `action_type`, `source_path`, `target_path`, `performed_at` | File Search & Organizer | MVP |
| `documents` | Store tracked document metadata | `id`, `path`, `title`, `document_type`, `indexed_at` | PDF & Document Assistant | MVP |
| `document_chunks` | Store extracted document text segments | `id`, `document_id`, `chunk_index`, `content` | PDF & Document Assistant | MVP |
| `permission_rules` | Store persisted permission and trust decisions | `id`, `action_type`, `scope`, `decision`, `updated_at` | Security & Permissions | MVP |
| `security_events` | Audit sensitive actions and decisions | `id`, `action_type`, `risk_level`, `decision`, `created_at` | Security & Permissions | MVP |
| `web_cache` | Cache free-source web responses | `id`, `cache_key`, `source`, `payload`, `expires_at` | Web Intelligence | MVP |
| `smart_devices` | Store future ESP32 device registry | `id`, `device_name`, `device_type`, `room`, `network_address`, `active` | Smart Home | Future |
| `automation_workflows` | Store reusable multi-step workflows | `id`, `name`, `description`, `active`, `created_at` | Automation Builder | V2 |
| `automation_steps` | Store ordered steps within workflows | `id`, `workflow_id`, `step_order`, `action_type`, `payload` | Automation Builder | V2 |

## Planning Notes

- SQLite is the local source of truth for MVP persistence.
- Tables should be introduced through migrations once implementation begins.
- Sensitive information should be minimized and stored only when needed.
- Frequently queried fields should receive indexes during implementation planning.

