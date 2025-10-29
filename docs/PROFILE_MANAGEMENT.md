# Profile Management Feature

## What It Is

The Profile Management system allows authenticated users to view and update their account information, change credentials, and delete their accounts. It provides a comprehensive dashboard with profile details, recent order history, and three separate forms for different types of updates (profile info, username, password).

## How It Works

### Profile Structure

The profile system consists of two related models:

1. **User Model** (`accounts.User`) - Authentication credentials
   - Username (login identifier)
   - Password (Argon2 hashed)
   - Email (AES-256-GCM encrypted)
   - Timestamps (join date, last login)

2. **Profile Model** (`accounts.Profile`) - Extended user information
   - Display name (how to address the user)
   - Phone number (contact information)
   - Favorite drink (personalization)
   - Bio (short description)

**Relationship**: OneToOne (each User has exactly one Profile)

### Step-by-Step Profile Access Flow

**1. User Visits Profile Page** (`/accounts/profile/`)
   - GET request → `accounts/views.py:172` (`profile_view`)
   - `@login_required` decorator checks authentication
   - If not logged in → Redirected to `/accounts/login/?next=/accounts/profile/`
   - If logged in → Profile page displayed

**2. Profile Data Loading** (`accounts/views.py:187`)
   ```python
   profile, _ = Profile.objects.get_or_create(
       user=request.user,
       defaults={"display_name": request.user.username}
   )
   ```
   - Gets existing profile OR creates new one (failsafe)
   - Signal should have created profile at signup, but this ensures it exists

**3. Forms Initialized** (`accounts/views.py:194`)
   - **ProfileForm**: Pre-filled with current profile data
   - **ChangeUsernameForm**: Empty (requires new username + password)
   - **ChangePasswordForm**: Empty (requires current + new passwords)

**4. Context Data Prepared** (`accounts/views.py:235`)
   ```python
   context = {
       "profile_form": profile_form,
       "username_form": username_form,
       "password_form": password_form,
       "update_success": False,
       "update_message": "",
       "user_email": request.user.email,
       "recent_orders": recent_orders[:3],
   }
   ```

**5. Template Rendered** (`templates/accounts/profile.html`)
   - Shows user info (username, email, join date, last login)
   - Displays three separate update forms
   - Shows recent orders (top 3)

### Profile Update Operations

#### Operation 1: Update Profile Info

**What Can Be Updated**:
- Display name (how baristas address you)
- Phone number (contact info)
- Favorite drink (default order)
- Bio (short description)

**Process** (`accounts/views.py:202`):

1. **User Submits Form**:
   ```html
   <form method="post">
       <input name="display_name" value="John Doe">
       <input name="phone_number" value="+1234567890">
       <input name="favorite_drink" value="Cappuccino">
       <textarea name="bio">Coffee enthusiast</textarea>
       <button name="update_profile">Save Profile</button>
   </form>
   ```

2. **View Detects Form Submission**:
   ```python
   if request.method == "POST" and "update_profile" in request.POST:
       if profile_form.is_valid():
           profile_form.save()  # Direct save, no validation needed
           update_success = True
           update_message = "Profile updated successfully."
   ```

3. **Validation**:
   - All fields optional (blank=True in model)
   - Phone number: Max 20 characters
   - Display name: Max 120 characters
   - No password required (updating profile info only)

4. **Database Update**:
   - `profile.save()` updates row in `accounts_profile` table
   - `updated_at` timestamp auto-updated
   - Changes immediately visible on refresh

#### Operation 2: Change Username

**Requirements**:
- New username (3-30 chars, alphanumeric with ._-)
- Current password (for verification)

**Process** (`accounts/views.py:209`):

1. **User Submits Form**:
   ```html
   <form method="post">
       <input name="new_username" value="newusername">
       <input type="password" name="password" value="current_password">
       <button name="change_username">Change Username</button>
   </form>
   ```

2. **View Detects Form Submission**:
   ```python
   elif request.method == "POST" and "change_username" in request.POST:
       username_form = ChangeUsernameForm(request.user, request.POST)
       if username_form.is_valid():
           request.user.username = username_form.cleaned_data["new_username"]
           request.user.save(update_fields=['username'])
           update_success = True
   ```

3. **Validation** (`accounts/forms.py:285`):
   ```python
   # Check format (3-30 chars, alphanumeric with ._-)
   if not USERNAME_PATTERN.match(username):
       raise ValidationError("Invalid format")

   # Check not same as current
   if username.lower() == self.user.username.lower():
       raise ValidationError("This is already your current username.")

   # Check not taken by another user
   if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
       raise ValidationError("That username is already taken.")

   # Verify password
   if not self.user.check_password(password):
       raise ValidationError("Incorrect password.")
   ```

4. **Database Update**:
   - `user.save(update_fields=['username'])` updates only username field
   - Session remains valid (user still logged in)
   - Navbar immediately shows new username

**Why Password Required?**
- Security: Prevents attackers from changing username if they gain temporary access
- Confirms user intent (not accidental)
- Standard security practice (similar to email change on most platforms)

#### Operation 3: Change Password

**Requirements**:
- Current password (for verification)
- New password (must meet strength requirements)
- Confirm new password (must match)

**Process** (`accounts/views.py:218`):

1. **User Submits Form**:
   ```html
   <form method="post">
       <input type="password" name="current_password" value="OldPass123!">
       <input type="password" name="new_password" value="NewPass456!">
       <input type="password" name="confirm_password" value="NewPass456!">
       <button name="change_password">Change Password</button>
   </form>
   ```

2. **View Detects Form Submission**:
   ```python
   elif request.method == "POST" and "change_password" in request.POST:
       password_form = ChangePasswordForm(request.user, request.POST)
       if password_form.is_valid():
           password_form.save()  # Hashes and saves new password
           update_session_auth_hash(request, request.user)  # CRITICAL!
           update_success = True
   ```

3. **Validation** (`accounts/forms.py:354`):
   ```python
   # Verify current password
   if not self.user.check_password(current_password):
       raise ValidationError("Current password is incorrect.")

   # Validate new password strength
   password_validation.validate_password(new_password, self.user)
   self._validate_password_strength(new_password)

   # Check passwords match
   if new_password != confirm_password:
       raise ValidationError("Passwords do not match.")
   ```

4. **Password Hashing** (`accounts/forms.py:430`):
   ```python
   # Hash new password with Argon2
   self.user.set_password(new_password)
   self.user.save(update_fields=['password'])
   ```

5. **Session Update** (`accounts/views.py:227`):
   ```python
   # CRITICAL: Update session hash to keep user logged in
   update_session_auth_hash(request, request.user)
   ```

**Why `update_session_auth_hash`?**
- Django includes password hash in session to detect compromised sessions
- Changing password invalidates session by default (logs user out)
- `update_session_auth_hash()` updates session with new hash
- Result: User stays logged in after password change

#### Operation 4: Delete Account

**Requirements**:
- Current password (for verification)
- Confirmation (modal dialog)

**Process** (`accounts/views.py:260`):

1. **User Clicks Delete Button**:
   - JavaScript modal appears: "Are you sure?"
   - User must enter password
   - Submits to `/accounts/profile/delete/` (POST only)

2. **View Verifies Password**:
   ```python
   password = request.POST.get("password", "")

   if not password:
       return redirect("accounts:profile")  # No password provided

   if not request.user.check_password(password):
       return redirect("accounts:profile")  # Wrong password
   ```

3. **Account Deletion** (`accounts/views.py:278`):
   ```python
   username = request.user.username  # Save for logging
   request.user.delete()  # CASCADE deletes profile too
   logout(request)  # End session
   return redirect("pages:home")
   ```

4. **Cascade Effects**:
   - User deleted from `accounts_user` table
   - Profile deleted (CASCADE) from `accounts_profile` table
   - Cart deleted (CASCADE) if exists
   - Orders deleted (CASCADE) - WARNING: Consider PROTECT in production!
   - AuthenticationEvents: User foreign key set to NULL (preserved for audit)

**Security Considerations**:
- POST only (prevents CSRF attacks)
- Password required (prevents accidental deletion)
- Confirmation modal (double-check user intent)
- Logout after deletion (session destroyed)
- Irreversible (no undo)

### Recent Orders Display

**Query** (`accounts/views.py:233`):
```python
recent_orders = request.user.orders.all()[:3]
```

**What's Shown**:
- Order number (order.id)
- Status (pending, confirmed, cancelled)
- Total amount
- Date placed
- **Note**: Orders feature not fully implemented yet (UI placeholder)

## Key Questions & Answers

### Q1: How is the profile created?

**A:** **Automatically via Django signal** when user signs up.

**Signal** (`accounts/models.py:346`):
```python
@receiver(post_save, sender=User)
def _ensure_profile(sender, instance: User, created: bool, **kwargs):
    if created:  # Only on new user creation
        Profile.objects.create(
            user=instance,
            display_name=instance.username  # Default to username
        )
```

**Process**:
1. User signs up → `User.objects.create_user()` called
2. User saved to database
3. Django fires `post_save` signal
4. `_ensure_profile` signal handler catches it
5. Profile created with `display_name = username`
6. OneToOne relationship established

**Failsafe** (`accounts/views.py:187`):
```python
profile, _ = Profile.objects.get_or_create(user=request.user, defaults={...})
```
- If signal somehow didn't fire, `get_or_create` creates profile
- Ensures every user always has a profile (no crashes)

### Q2: Why are there three separate forms instead of one?

**A:** **Security and user experience** considerations.

**Reasons**:

1. **Different Security Requirements**:
   - Profile info: No password needed (low risk)
   - Username change: Password required (medium risk)
   - Password change: Current password required (high risk)

2. **Different Validation Rules**:
   - Profile info: All optional, minimal validation
   - Username: Format check, uniqueness check, password verification
   - Password: Strength check, confirmation match, current password verification

3. **Clear User Intent**:
   - User explicitly chooses which update to make
   - Prevents accidental username/password changes
   - Each form has its own submit button

4. **Better Error Handling**:
   - Errors specific to each form
   - Don't mix profile validation errors with password errors
   - Clearer feedback to user

**Form Detection** (`accounts/views.py:202`):
```python
if request.method == "POST" and "update_profile" in request.POST:
    # Profile form submitted
elif request.method == "POST" and "change_username" in request.POST:
    # Username form submitted
elif request.method == "POST" and "change_password" in request.POST:
    # Password form submitted
```

### Q3: What happens if profile doesn't exist?

**A:** **Handled gracefully** with `get_or_create()`.

**Scenario 1: Normal Case** (profile exists)
```python
profile, created = Profile.objects.get_or_create(user=request.user)
# profile = existing Profile object
# created = False
```

**Scenario 2: Missing Profile** (signal failed somehow)
```python
profile, created = Profile.objects.get_or_create(
    user=request.user,
    defaults={"display_name": request.user.username}
)
# profile = newly created Profile object
# created = True
```

**Result**: User never sees error, profile always exists.

### Q4: Can users see their encrypted email?

**A:** **Yes, through decryption** in the view.

**Context Preparation** (`accounts/views.py:241`):
```python
context = {
    # ...
    "user_email": request.user.email,  # This triggers decryption
}
```

**Decryption** (`accounts/models.py:162`):
```python
@property
def email_decrypted(self) -> str:
    # Return cached value if available
    if self._email_cache:
        return self._email_cache

    # Decrypt from encrypted_email field
    if self.encrypted_email:
        self._email_cache = decrypt_email(self.encrypted_email)
        return self._email_cache

    # Fallback to plaintext (backwards compatibility)
    return self.email
```

**Template Display**:
```django
<p>Email: {{ user.email }}</p>
<!-- This calls user.email property, which returns email_decrypted -->
```

**Performance**: Decrypted once per request, cached in memory (`_email_cache`).

### Q5: How does changing password keep user logged in?

**A:** **Session auth hash update**.

**Problem**: Django includes password hash in session data to detect compromised sessions. Changing password invalidates session.

**Solution** (`accounts/views.py:227`):
```python
from django.contrib.auth import update_session_auth_hash

# After password change
update_session_auth_hash(request, request.user)
```

**What This Does**:
1. Calculates new session hash based on new password
2. Updates session data with new hash
3. User remains logged in with updated credentials

**Without This**:
```
1. User changes password
2. Password hash in session becomes stale
3. Django detects mismatch on next request
4. User logged out (forced to login again)
```

**With This**:
```
1. User changes password
2. Session hash updated immediately
3. Django sees valid session
4. User stays logged in
```

## Code References

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Profile View | `accounts/views.py:172` | Main profile page handler |
| Profile Form | `accounts/forms.py:224` | Profile info update form |
| Username Form | `accounts/forms.py:255` | Username change form |
| Password Form | `accounts/forms.py:319` | Password change form |
| Delete Account | `accounts/views.py:260` | Account deletion handler |
| Profile Model | `accounts/models.py:318` | Profile data model |
| Profile Signal | `accounts/models.py:346` | Auto-create profile on signup |
| Profile URL | `accounts/urls.py:69` | `/accounts/profile/` route |

## Edge Cases

### 1. What if user tries to change username to existing one?

**Scenario**: User "alice" tries to change username to "bob" (already exists).

**Handling** (`accounts/forms.py:304`):
```python
if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
    raise ValidationError("That username is already taken.")
```

**Result**: Form validation error, username not changed.

**Note**: `.exclude(pk=self.user.pk)` prevents error when user enters their own current username.

### 2. What if password change fails validation?

**Scenario**: User enters weak new password.

**Handling** (`accounts/forms.py:363`):
```python
try:
    password_validation.validate_password(new_password, self.user)
    self._validate_password_strength(new_password)
except ValidationError as exc:
    raise exc  # Show error to user
```

**Result**: Form shows validation errors, password not changed, user stays logged in.

### 3. What if user deletes account while logged in on multiple devices?

**Scenario**: User logged in on phone and laptop, deletes account on laptop.

**Handling**:
- Account deleted from database
- Laptop session destroyed immediately
- Phone session: On next request, `AuthenticationMiddleware` tries to load user
- User doesn't exist → `request.user` becomes `AnonymousUser`
- Phone automatically "logged out" (no manual logout needed)

**Result**: Account deleted, all sessions invalidated automatically.

### 4. What if profile form submitted with all blank fields?

**Scenario**: User submits profile form with empty display name, phone, etc.

**Handling** (`accounts/forms.py:240`):
```python
class ProfileForm(forms.ModelForm):
    class Meta:
        fields = ["display_name", "phone_number", "favorite_drink", "bio"]
        # All fields have blank=True in model
```

**Result**: Validation passes, profile saved with empty values. This is allowed.

### 5. What if username change password is wrong?

**Scenario**: User enters correct new username but wrong password.

**Handling** (`accounts/forms.py:313`):
```python
if not self.user.check_password(password):
    raise ValidationError("Incorrect password.")
```

**Result**: Form error "Incorrect password.", username not changed.

## Testing Guide

### Manual Testing Checklist

#### Test 1: View Profile
1. [ ] Log in with test account
2. [ ] Visit `/accounts/profile/`
3. [ ] **Expected**: Page shows:
   - [ ] Username
   - [ ] Email (decrypted)
   - [ ] Join date
   - [ ] Last login
   - [ ] Profile form (pre-filled if data exists)
   - [ ] Username change form (empty)
   - [ ] Password change form (empty)
   - [ ] Recent orders section (empty or sample data)

#### Test 2: Update Profile Info
1. [ ] Fill in profile form:
   - Display Name: "Test User"
   - Phone: "+1234567890"
   - Favorite Drink: "Cappuccino"
   - Bio: "Coffee lover"
2. [ ] Click "Save Profile"
3. [ ] **Expected**: Success message
4. [ ] Refresh page
5. [ ] **Expected**: Data still shown (persisted)
6. [ ] Check database:
   ```python
   from accounts.models import User
   u = User.objects.get(username='testuser')
   print(u.profile.display_name)  # Should show "Test User"
   ```

#### Test 3: Update Profile with Blank Fields
1. [ ] Clear all profile fields (leave blank)
2. [ ] Click "Save Profile"
3. [ ] **Expected**: Success (blank allowed)
4. [ ] Refresh page
5. [ ] **Expected**: Fields empty

#### Test 4: Change Username (Valid)
1. [ ] New Username: `newusername`
2. [ ] Password: `CurrentPass123!` (correct)
3. [ ] Click "Change Username"
4. [ ] **Expected**: Success message
5. [ ] **Verify**:
   - [ ] Navbar shows "newusername"
   - [ ] Still logged in
   - [ ] Can log out and log in with new username

#### Test 5: Change Username (Wrong Password)
1. [ ] New Username: `another`
2. [ ] Password: `wrongpassword`
3. [ ] Click "Change Username"
4. [ ] **Expected**: Error "Incorrect password."
5. [ ] **Verify**: Username not changed

#### Test 6: Change Username (Duplicate)
1. [ ] Create second user: `existing`
2. [ ] Log in as first user
3. [ ] Try changing username to: `existing`
4. [ ] **Expected**: Error "That username is already taken."

#### Test 7: Change Username (Invalid Format)
1. [ ] Try: `ab` (too short)
2. [ ] **Expected**: Error about format requirements
3. [ ] Try: `user@name` (invalid char)
4. [ ] **Expected**: Same format error

#### Test 8: Change Password (Valid)
1. [ ] Current Password: `OldPass123!`
2. [ ] New Password: `NewSecurePass456!`
3. [ ] Confirm: `NewSecurePass456!`
4. [ ] Click "Change Password"
5. [ ] **Expected**: Success message
6. [ ] **Verify**:
   - [ ] Still logged in (not logged out)
   - [ ] Can log out
   - [ ] Can log in with new password
   - [ ] Cannot log in with old password

#### Test 9: Change Password (Wrong Current)
1. [ ] Current Password: `wrongpassword`
2. [ ] New Password: `NewPass456!`
3. [ ] Confirm: `NewPass456!`
4. [ ] **Expected**: Error "Current password is incorrect."

#### Test 10: Change Password (Weak New)
1. [ ] Current Password: `CurrentPass123!`
2. [ ] New Password: `weak`
3. [ ] Confirm: `weak`
4. [ ] **Expected**: Validation errors (too short, etc.)

#### Test 11: Change Password (Mismatch)
1. [ ] Current Password: `CurrentPass123!`
2. [ ] New Password: `NewPass456!`
3. [ ] Confirm: `DifferentPass789!`
4. [ ] **Expected**: Error "Passwords do not match."

#### Test 12: Delete Account
1. [ ] Click "Delete Account" button
2. [ ] Modal appears
3. [ ] Enter password: `CurrentPass123!`
4. [ ] Confirm deletion
5. [ ] **Expected**:
   - [ ] Redirected to home page
   - [ ] Logged out
   - [ ] Navbar shows "Log In" / "Sign Up"
6. [ ] Try logging in with deleted username
7. [ ] **Expected**: "Invalid username or password."
8. [ ] Check database:
   ```python
   User.objects.filter(username='deleteduser').exists()  # False
   ```

#### Test 13: Delete Account (Wrong Password)
1. [ ] Click "Delete Account"
2. [ ] Enter password: `wrongpassword`
3. [ ] Confirm deletion
4. [ ] **Expected**: Redirected to profile, account NOT deleted

#### Test 14: Profile Auto-Creation
1. [ ] Create new user via Django shell:
   ```python
   from accounts.models import User
   u = User.objects.create_user('testuser2', 'test2@example.com', 'Pass123!')
   ```
2. [ ] Check profile exists:
   ```python
   u.profile  # Should not raise DoesNotExist
   print(u.profile.display_name)  # Should be 'testuser2'
   ```

### Automated Testing

Run profile tests:
```bash
python manage.py test accounts.tests.ProfileTestCase
```

**Test Coverage**:
- Profile view access
- Profile info update
- Username change (valid/invalid)
- Password change (valid/invalid)
- Account deletion
- Profile auto-creation signal

## Debugging Common Issues

### Issue 1: Profile DoesNotExist error

**Symptom**: `RelatedObjectDoesNotExist: User has no profile.`

**Cause**: Profile signal didn't fire or was bypassed.

**Solution**:
```python
# Option 1: Create profile manually
from accounts.models import Profile
profile = Profile.objects.create(user=user, display_name=user.username)

# Option 2: Use get_or_create (automatic failsafe)
profile, created = Profile.objects.get_or_create(
    user=user,
    defaults={"display_name": user.username}
)
```

### Issue 2: User logged out after password change

**Symptom**: Password change succeeds but user immediately logged out.

**Cause**: Missing `update_session_auth_hash()` call.

**Solution** (`accounts/views.py:227`):
```python
from django.contrib.auth import update_session_auth_hash

# After password change
update_session_auth_hash(request, request.user)
```

### Issue 3: Username change not showing immediately

**Symptom**: Username changes in database but navbar still shows old username.

**Cause**: Template caching or session issue.

**Solution**:
- Hard refresh browser (Ctrl+F5)
- Clear browser cache
- Check navbar template uses `{{ request.user.username }}`
- Verify `AuthenticationMiddleware` enabled

### Issue 4: Cannot delete account

**Symptom**: Delete button doesn't work or returns to profile.

**Cause**: Password check failing or CSRF issue.

**Debug**:
1. Check browser console for JavaScript errors
2. Check network tab for POST request to `/accounts/profile/delete/`
3. Check CSRF token present in form
4. Test with correct password

**Solution**:
- Ensure password correct
- Check `{% csrf_token %}` in modal form
- Verify `CsrfViewMiddleware` enabled

## Security Best Practices Followed

1. **Password Required for Sensitive Changes**:
   - Username change: Requires password
   - Account deletion: Requires password
   - Prevents unauthorized changes if session compromised

2. **Session Preservation**:
   - Password change doesn't log user out (`update_session_auth_hash`)
   - Better UX, user doesn't have to log in again

3. **Separate Forms**:
   - Different security levels for different operations
   - Clear user intent (no accidental changes)

4. **POST Only for Destructive Actions**:
   - Account deletion: POST only (CSRF protection)
   - Prevents accidental deletion via GET request

5. **Confirmation for Deletion**:
   - Modal dialog "Are you sure?"
   - Password required
   - Double-check prevents accidents

6. **Input Validation**:
   - Username format validation
   - Password strength validation
   - Server-side validation (client-side is UX only)

7. **Audit Trail**:
   - AuthenticationEvents preserved after user deletion (SET_NULL)
   - Username changes visible in updated_at timestamp
   - Consider adding ChangeLog model for comprehensive audit

## Future Enhancements

1. **Email Change**:
   - Add form to change email address
   - Require email verification (send confirmation link)
   - Require password for security

2. **Avatar/Profile Picture**:
   - Upload profile photo
   - Store in media folder or cloud storage
   - Display in navbar and profile page

3. **Two-Factor Authentication**:
   - Enable/disable 2FA
   - QR code for authenticator app
   - Backup codes

4. **Account History**:
   - Show login history (from AuthenticationEvents)
   - Show username change history
   - Show password change dates

5. **Privacy Settings**:
   - Control what other users can see
   - Public/private profile option
   - Data export (GDPR compliance)

6. **Notification Preferences**:
   - Email notifications on/off
   - Order updates
   - Marketing emails

7. **Connected Accounts**:
   - Link social media accounts
   - OAuth login (Google, Facebook)
   - Third-party integrations
