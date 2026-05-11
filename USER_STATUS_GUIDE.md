# User Status & Activity Tracking Guide

## Overview

The ISMS system now includes comprehensive user status tracking that correctly displays whether an intern is:
- **Online** (currently logged in) - Status: 🟢 Online, Action: Logout
- **Offline** (not logged in) - Status: 🔴 Offline, Action: Login

## How It Works

### Status Logic
- When a user **logs in**: A session record is created with `logout_time = NULL`
- When a user **logs out**: The session record is updated with `logout_time = <datetime>`
- If `logout_time IS NULL` → User is **Online**
- If `logout_time IS NOT NULL` → User is **Offline**

### Action Logic
- If user is **Online** → Action shown: "logout"
- If user is **Offline** → Action shown: "login"

---

## API Endpoints

### 1. Get Single User Status
**GET** `/api/user-status?username=<username>`

**Example:**
```bash
curl http://localhost:5000/api/user-status?username=john_intern
```

**Response (200 OK):**
```json
{
  "username": "john_intern",
  "status": "online",
  "action": "logout",
  "login_time": "2026-05-08 14:30:00",
  "last_activity": "2026-05-08 14:35:00",
  "email": "john@example.com",
  "domain": "example.com",
  "designation": "Intern"
}
```

### 2. Get All Active Users
**GET** `/api/active-users`

**Optional Parameters:**
- `role=USER` - Filter by role (e.g., USER, ADMIN, MANAGER)

**Example:**
```bash
curl http://localhost:5000/api/active-users
curl "http://localhost:5000/api/active-users?role=USER"
```

**Response (200 OK):**
```json
{
  "total": 3,
  "users": [
    {
      "username": "john_intern",
      "email": "john@example.com",
      "domain": "example.com",
      "designation": "Intern",
      "role": "USER",
      "status": "online",
      "action": "logout",
      "login_time": "2026-05-08 14:30:00",
      "last_activity": "2026-05-08 14:35:00"
    },
    {
      "username": "sarah_intern",
      "email": "sarah@example.com",
      "domain": "example.com",
      "designation": "Intern",
      "role": "USER",
      "status": "offline",
      "action": "login",
      "login_time": "2026-05-08 10:00:00",
      "last_activity": "2026-05-08 12:30:00"
    }
  ]
}
```

---

## Using the Test Script

### Check a Single User's Status

```bash
python test_user_status.py --username john_intern
```

**Output:**
```
📊 Getting status for: john_intern
   Endpoint: http://localhost:5000/api/user-status?username=john_intern

🟢 Status: ONLINE
   Action: logout
   Login Time: 2026-05-08 14:30:00
   Last Activity: 2026-05-08 14:35:00
   Email: john@example.com
   Domain: example.com
   Designation: Intern
```

### Get All Active Users

```bash
python test_user_status.py --all
```

**Output:**
```
👥 Getting all active users
   Endpoint: http://localhost:5000/api/active-users

✅ Found 3 user(s)

Username             Status     Action     Role            Last Activity
---------------------------------------------------------------------------
john_intern          🟢 online   logout     USER            2026-05-08 14:35:00
sarah_intern         🔴 offline  login      USER            2026-05-08 12:30:00
admin_user           🟢 online   logout     ADMIN           2026-05-08 14:40:00
```

### Get Users by Role

```bash
python test_user_status.py --all --role USER
```

### Interactive Mode

```bash
python test_user_status.py --interactive
```

---

## Dashboard Integration

The dashboard should display user status like this:

| DOMAIN | ROLE | STATUS | ACTION | IDLE TIME |
|--------|------|--------|--------|-----------|
| Python Developer | USER | 🟢 Online | logout | — |
| Data Analyst | USER | 🔴 Offline | login | — |
| Project Manager | ADMIN | 🟢 Online | logout | — |

### Fetching Status for Dashboard

```javascript
// JavaScript example for dashboard
async function refreshUserStatus() {
  try {
    const response = await fetch('http://localhost:5000/api/active-users');
    const data = await response.json();
    
    // Update table rows
    data.users.forEach(user => {
      const statusElement = document.querySelector(`[data-username="${user.username}"]`);
      if (statusElement) {
        // Update status badge
        const statusBadge = statusElement.querySelector('.status-badge');
        statusBadge.textContent = user.status.toUpperCase();
        statusBadge.className = `status-badge ${user.status === 'online' ? 'online' : 'offline'}`;
        
        // Update action button
        const actionBtn = statusElement.querySelector('.action-btn');
        actionBtn.textContent = user.action.toUpperCase();
      }
    });
  } catch (error) {
    console.error('Failed to fetch user status:', error);
  }
}

// Refresh every 30 seconds
setInterval(refreshUserStatus, 30000);
```

---

## Troubleshooting

### Status Shows "Offline" Even When User is Logged In

**Possible Causes:**

1. **Role Not Being Sent**
   - Ensure the agent is sending the `role` field in the login event
   - Check in API client that role is included in payload

2. **Session Record Not Created**
   - Check database: `SELECT * FROM activity WHERE username='john_intern' AND app_name='system' ORDER BY id DESC LIMIT 5;`
   - Verify `logout_time` is NULL for current session
   - Look for error messages in console logs

3. **Wrong Username Used**
   - Ensure the username in the database matches exactly what's displayed on dashboard
   - Check for extra spaces or case sensitivity

### Debug Steps

1. **Check the database directly:**
   ```sql
   SELECT id, username, role, login_time, logout_time, created_at 
   FROM activity 
   WHERE app_name='system' AND action='session' 
   ORDER BY id DESC 
   LIMIT 10;
   ```

2. **Test the API endpoint:**
   ```bash
   python test_user_status.py --username john_intern
   ```

3. **Check console logs:**
   - Look for "Activity logged successfully" message when logging in
   - Look for "Activity logged successfully" message with method=PATCH when logging out

4. **Verify role is captured:**
   ```sql
   SELECT username, role, status, login_time, logout_time 
   FROM (
     SELECT *, 
            CASE WHEN logout_time IS NULL THEN 'online' ELSE 'offline' END as status
     FROM activity 
     WHERE app_name='system' AND action='session'
   ) t 
   ORDER BY login_time DESC 
   LIMIT 10;
   ```

---

## Data Flow

### Login Event
```
1. User logs in via UI
   ↓
2. on_login_success() is called
   ↓
3. send_event("login", ...) is called
   ↓
4. API client gets current user data (including role)
   ↓
5. POST to /api/activity with action="login"
   ↓
6. Activity record created with logout_time=NULL
   ↓
7. Status = ONLINE, Action = LOGOUT
```

### Logout Event
```
1. User clicks Logout on logout screen
   ↓
2. on_logout() is called
   ↓
3. send_event("logout", ...) is called
   ↓
4. PATCH to /api/activity with action="logout"
   ↓
5. Activity record updated with logout_time=<current_time>
   ↓
6. Status = OFFLINE, Action = LOGIN
```

### Check User Status
```
1. Dashboard/Admin requests user status
   ↓
2. GET /api/user-status?username=john_intern
   ↓
3. Database queries for latest session record
   ↓
4. If logout_time IS NULL → status = online
   ↓
5. If logout_time IS NOT NULL → status = offline
   ↓
6. Return status, action, login_time, etc.
```

---

## Key Improvements Made

✅ Added `role` column to activity table
✅ Capture and store user role when logging in
✅ New GET endpoint `/api/user-status` to check individual user status
✅ New GET endpoint `/api/active-users` to list all users with their status
✅ Added role filter option for active users endpoint
✅ Created test script `test_user_status.py` for easy verification
✅ Fixed status display logic (online when logout_time IS NULL)
✅ Added action field (login/logout) based on current status

---

## Example Dashboard Update

If you have a web dashboard, here's how to integrate the status check:

```html
<!-- HTML -->
<table id="users-table">
  <thead>
    <tr>
      <th>Domain</th>
      <th>Role</th>
      <th>Status</th>
      <th>Action</th>
      <th>Idle Time</th>
    </tr>
  </thead>
  <tbody id="users-body">
    <!-- Rows will be populated by JavaScript -->
  </tbody>
</table>

<script>
  // Fetch and display user status
  async function loadUserStatus() {
    try {
      const response = await fetch('http://localhost:5000/api/active-users');
      const data = await response.json();
      
      const tbody = document.getElementById('users-body');
      tbody.innerHTML = '';
      
      data.users.forEach(user => {
        const row = document.createElement('tr');
        const statusClass = user.status === 'online' ? 'status-online' : 'status-offline';
        const statusEmoji = user.status === 'online' ? '🟢' : '🔴';
        
        row.innerHTML = `
          <td>${user.domain || '—'}</td>
          <td>${user.role || '—'}</td>
          <td><span class="${statusClass}">${statusEmoji} ${user.status.toUpperCase()}</span></td>
          <td>${user.action.toLowerCase()}</td>
          <td>—</td>
        `;
        
        tbody.appendChild(row);
      });
    } catch (error) {
      console.error('Failed to load user status:', error);
    }
  }
  
  // Load on page load
  loadUserStatus();
  
  // Refresh every 30 seconds
  setInterval(loadUserStatus, 30000);
</script>

<style>
  .status-online { color: green; font-weight: bold; }
  .status-offline { color: red; font-weight: bold; }
</style>
```

---

For more information or issues, check:
- Console logs (look for `[ACTIVITY]` prefix)
- Database tables: `logs` and `activity`
- API responses: Run test scripts with `--interactive` flag
