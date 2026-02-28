# InstagramClone — Frontend UX Design Spec

## User Story
As a social media user, I want an Instagram-like single-page web app where I can browse a global photo/video feed, create posts, like posts, comment, create a user account, and switch between users — all without leaving the page.

---

## User Flows

### Flow 1: Page Load → Browse Feed
```
Page loads
  └─→ Fetch GET /explore
        ├─→ Posts exist   → Render post cards in feed column
        └─→ No posts yet  → Show empty-state illustration + "Be the first to post!"
```

### Flow 2: User Creation
```
Header: click [+ New User]
  └─→ "Create Account" modal opens
        ├─→ Fill Username (required)
        ├─→ Fill Display Name (required)
        ├─→ Click [Create Account]
        │     ├─→ Validation error → inline error beneath field
        │     └─→ POST /users → success
        │             └─→ Modal closes
        │             └─→ New user added to User Switcher dropdown
        │             └─→ Toast: "Account created!"
        └─→ Click [✕] or Escape → modal closes, no changes
```

### Flow 3: Switch User
```
Header: User Switcher dropdown
  └─→ Select a user from list
        └─→ Fetch GET /users/{user_id}/feed
              ├─→ Posts exist   → Re-render feed with personalized posts
              └─→ No posts      → Empty state: "Follow someone to see their posts"
```

### Flow 4: Create Post
```
Feed: click [+ New Post] button (FAB or header button)
  └─→ "Create Post" modal opens
        ├─→ Fill Media URL (required)
        ├─→ Select Media Type (image/video toggle)
        ├─→ Fill Caption (optional, may include #hashtags)
        ├─→ Click [Share]
        │     ├─→ No user selected → inline error: "Select a user first"
        │     ├─→ Validation error → inline error beneath field
        │     └─→ POST /posts → success
        │             └─→ Modal closes
        │             └─→ Feed refreshes (re-fetches current feed)
        │             └─→ Toast: "Post shared!"
        └─→ Click [✕] or Escape → modal closes, no changes
```

### Flow 5: Like a Post
```
Post card: click [♡ Like] button
  └─→ No user selected → Toast: "Select a user to like posts"
  └─→ User selected    → POST /posts/{post_id}/like {user_id}
        ├─→ Success → heart fills (♥), like count increments (optimistic)
        └─→ Error   → heart reverts, error toast
```

### Flow 6: Comment on a Post
```
Post card: click [💬 comment count] or [Add a comment…] field
  └─→ Comment input expands below post card
  └─→ Type comment text
  └─→ Press Enter or click [Post]
        ├─→ No user selected → Toast: "Select a user to comment"
        └─→ POST /posts/{post_id}/comments {user_id, text}
              └─→ Success → comment appears in list, input clears
```

---

## Screens & Wireframes

### Screen: Main Layout (Desktop — 1024px+)

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER (fixed, full-width)                                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 📸 Instagramᶜˡᵒⁿᵉ    [User Switcher ▾]  [+ New Post]     │  │
│  └────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   LEFT SPACER      FEED COLUMN (max-width 600px)   RIGHT SPACER  │
│                   ┌──────────────────────────┐                   │
│                   │  ┌────────────────────┐  │                   │
│                   │  │  POST CARD         │  │                   │
│                   │  │  [avatar] username │  │                   │
│                   │  │  ┌──────────────┐  │  │                   │
│                   │  │  │ media area   │  │  │                   │
│                   │  │  │ (img/video)  │  │  │                   │
│                   │  │  └──────────────┘  │  │                   │
│                   │  │  ♥ 42  💬 7        │  │                   │
│                   │  │  caption text…     │  │                   │
│                   │  │  #hashtag #photo   │  │                   │
│                   │  │  [Add a comment…]  │  │                   │
│                   │  └────────────────────┘  │                   │
│                   │  ┌────────────────────┐  │                   │
│                   │  │  POST CARD …       │  │                   │
│                   │  └────────────────────┘  │                   │
│                   └──────────────────────────┘                   │
│                                                                    │
│                   [+ New Post] FAB (bottom-right, mobile only)   │
└──────────────────────────────────────────────────────────────────┘
```

### Screen: Post Card (detail)

```
┌──────────────────────────────────────────────────────┐
│  [●] username · display_name            ··· (menu)   │  ← card header
│      2 hours ago                                      │
├──────────────────────────────────────────────────────┤
│                                                        │
│   ┌──────────────────────────────────────────────┐   │
│   │                                              │   │
│   │          media (img tag or video tag)        │   │  ← square ratio
│   │            aspect-ratio: 1/1                 │   │
│   │                                              │   │
│   └──────────────────────────────────────────────┘   │
│                                                        │
│  [♡] 42 likes   [💬] 7 comments                      │  ← action row
│                                                        │
│  username: caption text goes here…                    │  ← caption
│  #sunset #travel #photo                               │  ← hashtags (blue)
│                                                        │
│  View all 7 comments ›                                │  ← comment toggle
│  ┌────────────────────────────────────────────────┐  │
│  │ [●] Add a comment…                     [Post]  │  │  ← comment input
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Screen: Header / Nav Bar

```
┌────────────────────────────────────────────────────────────────┐
│                                                                  │
│  📸 Instagramᶜˡᵒⁿᵉ        [● No user ▾]      [+ New Post]    │
│                               (dropdown)        (gradient btn)  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
Gradient: left=#405DE6, mid=#833AB4 / #C13584, right=#F77737 / #FCAF45
Height: 56px. Logo: bold italic, white. Right cluster: gap 12px.
```

### Screen: User Switcher Dropdown (open)

```
[● alice_w ▾]
┌─────────────────────────────┐
│  ● alice_w  Alice Williams  │  ← currently selected (bold)
│  ○ bob_j    Bob Jones       │
│  ○ carol_m  Carol Martinez  │
│  ─────────────────────────  │
│  [+ Create new user]        │
└─────────────────────────────┘
```

### Screen: Create Post Modal

```
┌─────────────────────────────────────────────────────┐
│  Share a new post                              [✕]   │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Media URL *                                          │
│  ┌─────────────────────────────────────────────┐    │
│  │ https://example.com/photo.jpg               │    │
│  └─────────────────────────────────────────────┘    │
│  [error text if blank]                               │
│                                                       │
│  Media Type *                                         │
│  ┌──────────┐ ┌──────────┐                           │
│  │  📷 Image │ │  🎬 Video │   ← segmented control    │
│  └──────────┘ └──────────┘                           │
│   (selected tab has gradient fill + white text)      │
│                                                       │
│  Caption                                              │
│  ┌─────────────────────────────────────────────┐    │
│  │                                             │    │
│  │  Use #hashtags to categorize your post      │    │  ← 3-row textarea
│  │                                             │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  [          Share          ]  ← full-width gradient  │
│                                                       │
└─────────────────────────────────────────────────────┘
Backdrop: rgba(0,0,0,0.6). Modal: white, border-radius 16px, max-width 480px.
```

### Screen: Create User Modal

```
┌─────────────────────────────────────────────────────┐
│  Create account                                [✕]   │
├─────────────────────────────────────────────────────┤
│                                                       │
│  Username *  (no spaces)                              │
│  ┌─────────────────────────────────────────────┐    │
│  │ john_doe                                    │    │
│  └─────────────────────────────────────────────┘    │
│  [error text if blank / taken]                       │
│                                                       │
│  Display Name *                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │ John Doe                                    │    │
│  └─────────────────────────────────────────────┘    │
│  [error text if blank]                               │
│                                                       │
│  [          Create Account          ]                │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Screen: Empty State (no posts)

```
┌──────────────────────────────────────────────────────┐
│                                                        │
│                       📷                              │
│                                                        │
│              No posts yet.                            │
│         Be the first to share something!              │
│                                                        │
│          [  + Create your first post  ]               │
│                                                        │
└──────────────────────────────────────────────────────┘
Icon: 5rem. Heading: 1.2rem, #262626. Sub: 0.9rem, #8e8e8e.
```

### Screen: Mobile Layout (< 600px)

```
┌──────────────────────────┐
│ 📸 Instagramᶜˡᵒⁿᵉ  [●▾]  │  ← [+ New Post] moved to FAB
├──────────────────────────┤
│  ┌────────────────────┐  │
│  │   POST CARD        │  │
│  │   full-width       │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │   POST CARD        │  │
│  └────────────────────┘  │
│                           │
│              [+]          │  ← FAB: 56px circle, gradient, bottom-right
└──────────────────────────┘
```

---

## Component Specs

| Component | States | Behavior |
|---|---|---|
| **Header** | default | Fixed top, full-width, gradient background, 56px height. Contains logo, user switcher, new-post button |
| **User Switcher** | closed / open / no-users | Dropdown showing all users from `GET /users` (polled on load + after user creation). Selecting a user re-fetches feed. "No user selected" is default state |
| **Post Card** | default / liked / loading | White card, 1px #dbdbdb border, border-radius 8px, no horizontal margin on mobile |
| **Post Avatar** | default | 32px circle, generated gradient background with user initial letter if no profile_pic_url |
| **Media Area** | image / video / loading | aspect-ratio 1/1, object-fit cover. Image: `<img>` tag. Video: `<video controls>` tag. Loading: shimmer animation |
| **Like Button** | unliked / liked / loading | ♡ (unliked, #262626) → ♥ (liked, #ed4956 red). Optimistic update: flip immediately, revert on error. Disabled while loading |
| **Comment Toggle** | collapsed / expanded | "View all N comments" link expands comment list section. Fetches `GET /posts/{post_id}/comments` on expand |
| **Comment Input** | empty / filled / submitting | Placeholder "Add a comment…". Enter key or [Post] button submits. Clears on success. Shows spinner while submitting |
| **Hashtag** | default | Inline `#tag` words in caption rendered as `<span class="hashtag">` — color #00376b (Instagram blue). Non-clickable (v1) |
| **Create Post Button** | default / hover / disabled | Gradient fill. Disabled while submitting (opacity 0.6, cursor not-allowed). Shows "Sharing…" text while loading |
| **Create User Button** | default / hover / disabled | Same disabled pattern as Create Post |
| **Modal Backdrop** | open / closing | rgba(0,0,0,0.6). Click-outside closes modal. Escape key closes modal |
| **Toast** | success / error | Bottom-center, slides up from bottom, auto-dismiss after 3s. Success: #12b668 bg. Error: #ed4956 bg. White text |
| **FAB (mobile)** | default / hover | 56px circle, fixed bottom-right (20px margin), gradient background, white + icon |
| **Loading Shimmer** | active | Applied to feed while fetching. 3 placeholder card skeletons with animated grey gradient sweep |
| **Timestamp** | default | "N hours ago" / "N days ago" relative time. Computed client-side from post.created_at |

---

## Interaction Notes

- **Loading state:** On any feed fetch, show 3 skeleton card shimmer placeholders. Replace with real cards when data arrives. Buttons that trigger fetches show an inline spinner and become disabled.

- **Empty state (no posts in feed):** Show centered camera emoji + heading "No posts yet" + CTA button. Three distinct variants:
  1. Global explore with no posts at all → "Be the first to post!"
  2. Personalized feed, user follows nobody with posts → "Follow someone to see their posts here"
  3. API error → "Couldn't load posts. Try again" + [Retry] button

- **Error state:** API call failures show a toast (red bg) with a brief message. Forms show inline field-level errors in red `#ed4956` text below the invalid field. Network errors never leave the UI in a broken state.

- **Success feedback:** Action toasts appear bottom-center, slide up, and auto-dismiss after 3 seconds. Like count updates are optimistic (instant visual feedback; no toast needed for likes).

- **Hover/focus:**
  - Buttons: brightness(0.92) on hover, `outline: 2px solid #405DE6` on keyboard focus (accessible focus ring)
  - Post card: subtle `box-shadow: 0 2px 8px rgba(0,0,0,0.08)` on hover
  - Like button: scales to 1.15 with `transform: scale(1.15)` on hover
  - Input fields: `border-color: #405DE6` on focus, no outline (custom border replaces it)

- **User switcher selection:** Persists in JS state (`currentUserId`). All subsequent post/like/comment actions use this ID. Visual indicator shows selected user's initial in header circle.

- **Scroll:** Feed scrolls natively; header stays fixed. No infinite scroll in v1 — all posts loaded at once.

- **Media URL validation:** No URL format enforcement in the frontend (backend validates). Media that fails to load shows a grey placeholder with 🖼️ icon.

- **Timestamp formatting:** Times within 1 hour → "X min ago". Within 24h → "X hours ago". Otherwise → "X days ago". No absolute dates in v1.

---

## Color & Typography

### Color Palette
```
Primary gradient: linear-gradient(135deg, #405DE6, #833AB4, #C13584, #F77737, #FCAF45)
  Used for: header background, CTA buttons, FAB, active media type toggle
  Condensed (button): linear-gradient(135deg, #405DE6, #C13584)

Like red:         #ed4956   — liked heart, error text
Link blue:        #00376b   — hashtags, "View all comments" link
Background:       #fafafa   — page background
Card:             #ffffff   — post card background
Border:           #dbdbdb   — card border, input border, dividers
Text primary:     #262626   — usernames, body text
Text secondary:   #8e8e8e   — timestamps, muted captions, placeholders
Text on gradient: #ffffff   — header logo, button text
Success toast:    #12b668
Error toast bg:   #ed4956
```

### Typography
```
Font stack: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
(Matches Instagram's native rendering on each OS — no external font load)

Sizes:
  Logo:             1.4rem, bold, italic
  Username (card):  0.875rem (14px), font-weight 600
  Caption:          0.875rem (14px), font-weight 400
  Hashtag:          0.875rem (14px), color #00376b
  Timestamp:        0.75rem (12px), color #8e8e8e
  Like/comment count: 0.875rem (14px), font-weight 600
  Modal heading:    1rem (16px), font-weight 600
  Input label:      0.875rem (14px), font-weight 600
  Input text:       0.9375rem (15px)
  Toast:            0.875rem (14px)
```

### Spacing
```
Spacing unit: 8px
  Card padding:       16px (2 units)
  Card margin-bottom: 24px (3 units)
  Header padding-x:   16px
  Modal padding:      24px (3 units)
  Form field gap:     16px (2 units)
  Action row gap:     12px (1.5 units)
```

---

## Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| `< 600px` (mobile) | Feed is full-width (no side margins). [+ New Post] button hidden from header, shown as FAB. Cards have 0 border-radius |
| `600px – 935px` (tablet) | Feed centered, max-width 600px. Header button visible. No sidebar |
| `> 935px` (desktop) | Feed centered, max-width 600px. Comfortable side whitespace |

No sidebar in v1 — the PO spec only mentions the feed column. Sidebar can be added in v2.

---

## API Mapping

| User action | API call | On success | On error |
|---|---|---|---|
| Page load | `GET /explore` | Render posts | Error empty state + retry |
| Select user in switcher | `GET /users/{user_id}/feed` | Refresh feed | Toast error |
| Create user [submit] | `POST /users` | Add to switcher, toast | Inline field error |
| Create post [Share] | `POST /posts` | Refresh feed, toast | Inline / toast |
| Click ♡ like | `POST /posts/{post_id}/like` | Heart fills, count +1 (optimistic) | Revert, toast |
| View comments | `GET /posts/{post_id}/comments` | Render comment list | Inline error |
| Submit comment | `POST /posts/{post_id}/comments` | Append comment, clear input | Toast |
| Load user switcher | `GET /users` — **Note:** no such endpoint in spec; JS fetches users by storing known users in a local array that grows as users are created. Initial load seeds from `/explore` post authors. | N/A | N/A |

### User Switcher Population Strategy
Since there is no `GET /users` (list-all) endpoint, the frontend builds the user list from:
1. Authors seen in posts returned by `/explore` on page load
2. Users created during the session (POST /users response)

This is intentional to avoid requiring a new backend endpoint. The dropdown starts empty (or "No user / Browse as guest") and populates as the app is used.

---

## Open Questions
- [ ] Should the like button toggle (unlike on second tap)? The backend supports `DELETE /posts/{post_id}/like` — implementing toggle would require tracking liked state client-side per user+post. **Recommendation: implement toggle in v1, track in a JS Set.**
- [ ] Should comment list load eagerly (on card render) or lazily (on expand)? **Recommendation: lazy — avoids N+1 fetch on page load.**
