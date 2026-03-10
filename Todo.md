Mirror Assistant Chatbot
1. Purpose

This document defines the software specification for the Mirror Assistant Chatbot used by mental health professionals. The initial focus is on a schedule management chatbot for mental health professionals. It covers the chatbot workflows, system behaviour, functional requirements, data requirements, business rules, and APIs for schedule and booking related operations only. [Login, authentication and onboarding are out of scope.]


2. Scope

The Schedule Management Chatbot enables a mental health professional to manage availability and appointments through a conversational interface.
This module includes:

* opening booking slots
* editing booking slots
* deleting booking slots
* creating bookings
* editing bookings
* deleting bookings
* fetching schedule for a day
* fetching schedule for a specific client
* viewing upcoming sessions
* handling schedule conflicts and booking constraints



3. Objectives

The system shall:

* reduce manual effort in managing appointment schedules
* provide a fast conversational interface for slot and booking management
* ensure scheduling consistency and conflict prevention
* allow retrieval of schedules by date and by client
* support clear, low friction actions for professionals



4. User Role

Primary User - Mental Health Professional
The professional can:

* create availability slots
* modify or remove availability slots
* create, edit, reschedule, and cancel bookings
* retrieve schedule views
* filter schedule by client



5. System Context

The chatbot acts as the interaction layer between the professional and the scheduling system.
The chatbot shall:

* receive structured or natural language scheduling instructions
* interpret intent
* validate data
* execute scheduling actions against backend services
* return clear success, failure, or conflict responses



6. High Level Features

6.1 Availability Slot Management

The system shall allow the user to:

* open a booking slot
* edit a booking slot
* delete a booking slot
* view available slots for a selected date

6.2 Booking Management

The system shall allow the user to:

* create a booking in an available slot
* edit a booking
* reschedule a booking
* delete or cancel a booking
* view booking details

6.3 Schedule Retrieval

The system shall allow the user to:

* fetch full schedule for a selected day
* fetch schedule filtered by client
* fetch upcoming sessions
* fetch free and booked slots for a day



7. Functional Requirements

The chatbot shall provide the following schedule management menu options:

1. Open booking slot
2. Edit booking slot
3. Delete booking slot
4. Create booking
5. Edit booking
6. Delete booking
7. View today’s schedule
8. View schedule by date
9. View schedule by client
10. View upcoming bookings

The chatbot may support both menu driven interaction and natural language commands.


7.1 Open Booking Slot

The system shall allow the professional to create an availability slot by providing:

* date
* start time
* end time
* optional recurrence flag if enabled in later release
* optional notes or slot type if required later

Validation rules:

* end time must be later than start time
* slot must not overlap with another active slot unless explicitly permitted
* slot must not be created in the past
* slot duration must conform to allowed minimum and maximum values
* slot must belong to the professional’s working schedule rules if such rules exist

Expected response:

* slot created successfully
* conflict detected
* invalid date or time
* missing required input



7.2 Edit Booking Slot

The system shall allow the professional to modify an existing slot.
Editable fields:

* date
* start time
* end time
* slot status where permitted

Validation rules:

* updated slot must not overlap with another slot
* if the slot has a linked booking, edit rules must respect booking constraints
* system must block unsafe edits that would orphan or invalidate an active booking

Expected response:

* slot updated successfully
* update blocked due to active booking
* conflict detected
* invalid slot identifier



7.3 Delete Booking Slot

The system shall allow the professional to delete an existing slot.
Validation rules:

* if the slot has no active booking, deletion may proceed
* if the slot has an active booking, the system shall either block deletion or require booking cancellation or reassignment based on business policy

Expected response:

* slot deleted successfully
* deletion blocked due to active booking
* invalid slot identifier



7.4 Create Booking

The system shall allow the professional to create a booking by providing:

* client identifier
* date
* start time
* end time or slot selection
* optional booking notes
* optional session type if supported

Validation rules:

* booking must map to an available slot
* booking must not overlap with another booking for the same professional
* booking must not be created in the past
* client must exist in the system
* slot status must be available at the moment of booking

Expected response:

* booking created successfully
* selected slot unavailable
* client not found
* invalid time range
* duplicate or conflicting booking



7.5 Edit Booking

The system shall allow the professional to edit an existing booking.
Editable fields:

* client
* date
* time
* slot mapping
* booking status
* internal non clinical note related to appointment if permitted

Validation rules:

* updated booking must still map to an available slot
* updated booking must not overlap another booking
* invalid client or invalid slot references must be rejected

Expected response:

* booking updated successfully
* update blocked by conflict
* target slot unavailable
* invalid booking identifier



7.6 Delete Booking

The system shall allow the professional to cancel or delete a booking.
Validation rules:

* booking must exist
* if policy requires, the system shall record cancellation reason or status instead of hard deleting
* linked slot may be reopened automatically after cancellation if business rules permit

Expected response:

* booking cancelled successfully
* booking deleted successfully
* invalid booking identifier



7.7 Fetch Schedule for Day

The system shall allow the professional to request their full schedule for a specified date.
Output shall include:

* booked sessions
* open slots
* blocked or unavailable periods if applicable
* client name for booked sessions
* start and end times
* booking status

Supported examples:

* today’s schedule
* tomorrow’s schedule
* schedule for 18 March

Expected response:

* ordered day timeline
* no schedule found
* invalid date input



7.8 Fetch Schedule by Client

The system shall allow the professional to retrieve bookings associated with a specific client.
Search inputs:

* client name
* client ID
* client phone or unique handle if supported

Output shall include:

* upcoming bookings with that client
* past bookings if allowed in the view
* date and time of each appointment
* booking status

Expected response:

* matching schedule entries returned
* client not found
* no bookings for selected client



7.9 View Upcoming Bookings

The system shall allow retrieval of upcoming appointments across a default future window.
Default sort order:

* ascending by date and time

Output shall include:

* date
* start time
* end time
* client name
* booking status



8. Conversation Design Requirements

The chatbot shall support concise and deterministic conversational flows.

8.1 Interaction Principles

* ask only for missing data needed to complete an action
* confirm destructive actions such as slot deletion or booking cancellation
* return a clear summary after every successful action
* provide direct corrective guidance on validation failure
* maintain context for the current scheduling task

8.2 Sample Intents

Supported intents include:

* open slot on Monday from 3 PM to 5 PM
* move my 4 PM booking with Anjali to 6 PM
* show my schedule for today
* delete my 2 PM slot tomorrow
* find sessions with Ravi this week

8.3 Clarification Rules

The chatbot shall ask for clarification only when:

* date is ambiguous
* time is ambiguous
* multiple clients match input
* multiple bookings match requested action
* requested action conflicts with existing data



9. Tech

Frontend

* Next.js
* Tailwind CSS
* TypeScript

Backend and AI

* Python 3.14
* FastAPI for APIs
* Supabase (Local setup)
* Groq for LLM



Project Structure
```
mirror_assistant_frontend/
│
├── public/
│   ├── icons/
│   ├── images/
│   └── fonts/
│
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── chatbot/
│   │   ├── schedules/
│   │   ├── bookings/
│   │   └── clients/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── chatbot/
│   │   ├── schedule/
│   │   └── shared/
│   │
│   ├── lib/
│   │   ├── api.ts
│   │   ├── utils.ts
│   │   └── constants.ts
│   │
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useSchedule.ts
│   │   └── useBookings.ts
│   │
│   ├── services/
│   │   ├── chatbot.service.ts
│   │   ├── schedule.service.ts
│   │   └── booking.service.ts
│   │
│   ├── types/
│   │   ├── chatbot.ts
│   │   ├── schedule.ts
│   │   └── booking.ts
│   │
│   ├── styles/
│   │   └── globals.css
│   │
│   └── context/
│       └── app-context.tsx
│
├── tailwind.config.ts
├── tsconfig.json
├── next.config.js
├── package.json
└── README.md
```

```
mirror_assistant_backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chatbot.py
│   │   │   ├── schedules.py
│   │   │   ├── bookings.py
│   │   │   └── clients.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── constants.py
│   │
│   ├── services/
│   │   ├── chatbot_service.py
│   │   ├── schedule_service.py
│   │   ├── booking_service.py
│   │   ├── client_service.py
│   │   └── ai_service.py
│   │
│   ├── models/
│   │   ├── schedule.py
│   │   ├── booking.py
│   │   ├── client.py
│   │   └── chatbot.py
│   │
│   ├── schemas/
│   │   ├── schedule.py
│   │   ├── booking.py
│   │   ├── client.py
│   │   └── chatbot.py
│   │
│   ├── db/
│   │   ├── supabase.py
│   │   └── repositories/
│   │       ├── schedule_repository.py
│   │       ├── booking_repository.py
│   │       └── client_repository.py
│   │
│   ├── agents/
│   │   ├── intent_parser.py
│   │   ├── response_builder.py
│   │   └── workflow_manager.py
│   │
│   └── utils/
│       ├── datetime_utils.py
│       ├── validators.py
│       └── logger.py
│
├── tests/
│   ├── test_chatbot.py
│   ├── test_schedules.py
│   ├── test_bookings.py
│   └── test_clients.py
│
├── requirements.txt
├── .env
└── README.md
```
---

10. Data Model

10.1 AvailabilitySlot

Fields:

* slot_id
* professional_id
* date
* start_time
* end_time
* status
* created_at
* updated_at

Allowed status values:

* available
* booked
* blocked
* cancelled

10.2 Booking

Fields:

* booking_id
* professional_id
* client_id
* slot_id
* date
* start_time
* end_time
* status
* booking_note
* created_at
* updated_at

Allowed status values:

* scheduled
* rescheduled
* cancelled
* completed
* no_show

10.3 Client Reference

Fields required for schedule linkage:

* client_id
* client_name



11. Business Rules

* a booking shall not exist without a valid professional reference
* a booking shall not overlap another active booking for the same professional
* a booking shall only be created against an available slot unless override is explicitly supported
* deleting a slot with an active booking shall be blocked or routed through a cancellation workflow
* editing a slot linked to an active booking shall be restricted
* all schedule views shall return time ordered results
* schedule data shown in chatbot responses shall be limited to necessary fields only
* past date slot creation shall not be allowed
* system time zone must be consistent and explicit



12. API Level Logical Specification

12.1 Create Slot

Method: POST
Endpoint: /schedule/slots
Request:

* professional_id
* date
* start_time
* end_time

Response:

* slot_id
* status
* created slot details
* error details if failed

12.2 Update Slot

Method: PUT
Endpoint: /schedule/slots/{slot_id}
Request:

* date
* start_time
* end_time
* status if permitted

Response:

* updated slot details
* validation or conflict error

12.3 Delete Slot

Method: DELETE
Endpoint: /schedule/slots/{slot_id}
Response:

* success state
* deletion blocked reason if applicable

12.4 Create Booking

Method: POST
Endpoint: /schedule/bookings
Request:

* professional_id
* client_id
* slot_id or date plus time
* booking_note optional

Response:

* booking_id
* status
* booking details
* validation or conflict error

12.5 Update Booking

Method: PUT
Endpoint: /schedule/bookings/{booking_id}
Response:

* updated booking details
* validation or conflict error

12.6 Delete Booking

Method: DELETE
Endpoint: /schedule/bookings/{booking_id}
Response:

* success state
* cancellation state
* failure reason

12.7 Get Day Schedule

Method: GET
Endpoint: /schedule/day
Query params:

* professional_id
* date

Response:

* list of day schedule entries
* open slots
* booked slots
* booking statuses

12.8 Get Schedule by Client

Method: GET
Endpoint: /schedule/client/{client_id}
Response:

* list of bookings for that client
* upcoming and past entries based on business policy

13. Error Handling Requirements


The system shall provide structured error responses for:

* missing required fields
* invalid date
* invalid time
* slot conflict
* booking conflict
* slot unavailable
* booking not found
* client not found
* action blocked by business rule
* internal system failure

Error messages shown in chat shall be user readable and action oriented.
Examples:

* This slot overlaps with an existing slot from 3:00 PM to 4:00 PM.
* The selected booking cannot be moved because the new time is unavailable.
* No client matched that name. Please choose from the listed results.

