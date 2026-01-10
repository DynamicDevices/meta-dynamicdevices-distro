# NetworkManager Patch Requirements

## Critical Configuration Requirement

**⚠️ IMPORTANT**: The NetworkManager patch (`0001-wifi-dont-clear-secrets-if-stored-in-keyfile.patch`) **REQUIRES** all WiFi connections to have `psk-flags=0` to function correctly.

## What the Patch Does

The patch prevents NetworkManager from clearing WiFi secrets when a 4-way handshake fails, allowing retry with the existing PSK instead of requesting new secrets from a non-existent secret agent.

## Required Configuration

### 1. Connection-Level: `psk-flags=0` (MANDATORY)

**Every WiFi connection MUST have:**
```bash
802-11-wireless-security.psk-flags 0
# OR
wifi-sec.psk-flags 0
```

**Why:** The patch checks if secrets are stored in the connection file by examining the secret flags. If `psk-flags=0` is not set, the patch will not activate and NetworkManager will fall back to the original behavior (clears secrets, requests new ones from agent).

**Values:**
- `0` = Secret saved in connection file ✅ **REQUIRED**
- `1` = Secret agent-owned (not saved) ❌ **WILL NOT WORK WITH PATCH**
- `2` = Secret not required ❌ **WILL NOT WORK WITH PATCH**

### 2. System-Level: Keyfile Plugin (MANDATORY)

**NetworkManager.conf MUST have:**
```ini
[main]
plugins=keyfile
```

**Why:** Without the keyfile plugin, NetworkManager may not properly store secrets in connection files, even with `psk-flags=0`.

### 3. Connection Persistence: `nmcli connection save` (MANDATORY)

**After creating or modifying a connection, MUST call:**
```bash
nmcli connection save <ConnectionName>
```

**Why:** This ensures the `psk-flags=0` setting is persisted to disk and available when NetworkManager loads the connection.

## Connection Creation Examples

### ✅ CORRECT: With psk-flags=0

```bash
# Create connection
nmcli con add type wifi \
    con-name MyWiFi \
    ssid "MySSID" \
    802-11-wireless-security.key-mgmt WPA-PSK \
    802-11-wireless-security.psk "password" \
    802-11-wireless-security.psk-flags 0 \
    connection.autoconnect yes \
    connection.autoconnect-retries -1 \
    connection.auth-retries -1 \
    connection.permissions ""

# Save connection (REQUIRED)
nmcli connection save MyWiFi
```

### ❌ INCORRECT: Missing psk-flags=0

```bash
# This will NOT work with the patch!
nmcli con add type wifi \
    con-name MyWiFi \
    ssid "MySSID" \
    802-11-wireless-security.psk "password"
# Missing: 802-11-wireless-security.psk-flags 0
# Missing: nmcli connection save MyWiFi
```

## Connection Modification Examples

### ✅ CORRECT: Always set psk-flags=0

```bash
nmcli connection modify MyWiFi \
    802-11-wireless-security.psk-flags 0

# Save connection (REQUIRED)
nmcli connection save MyWiFi
```

### ❌ INCORRECT: Forgetting psk-flags

```bash
# This may reset psk-flags to default (agent-owned)
nmcli connection modify MyWiFi \
    802-11-wireless-security.psk "newpassword"
# Missing: 802-11-wireless-security.psk-flags 0
# Missing: nmcli connection save MyWiFi
```

## Verification

To verify a connection has the correct configuration:

```bash
# Check psk-flags
nmcli connection show <ConnectionName> | grep -i "psk-flags"
# Should show: 802-11-wireless-security.psk-flags:0

# Check connection file
cat /etc/NetworkManager/system-connections/<ConnectionName>.nmconnection | grep -i psk
# Should show: psk=<password> and psk-flags=0
```

## Impact of Missing Configuration

If a connection is created/modified without `psk-flags=0`:

1. **Patch will NOT activate** - Falls back to original NetworkManager behavior
2. **4-way handshake failure** → NetworkManager clears secrets
3. **NetworkManager requests new secrets** from non-existent secret agent
4. **"No secrets" error** → Connection fails permanently
5. **No auto-reconnection** → Manual intervention required

## All Connection Creation/Modification Paths

Ensure ALL of these paths set `psk-flags=0`:

1. ✅ `meta-subscriber-overrides/recipes-support/default-network-manager/default-network-manager/setup-default-connections.sh`
2. ✅ `meta-subscriber-overrides/recipes-devtools/python/python3-improv/imx8mm-jaguar-sentai/onboarding-server.py`
3. ⚠️ Any custom scripts or applications that create WiFi connections
4. ⚠️ Manual `nmcli` commands
5. ⚠️ GUI tools (if used)

## Testing

To test if the patch is working:

1. Create a connection with `psk-flags=0`
2. Connect to WiFi
3. Temporarily disable the access point (simulate 4-way handshake failure)
4. Re-enable the access point
5. **Expected:** Connection should automatically reconnect
6. **Check logs:** Should see "secrets are in file. Retrying with existing PSK" message

## References

- Patch: `0001-wifi-dont-clear-secrets-if-stored-in-keyfile.patch`
- Analysis: `NETWORKMANAGER_PATCH_CONFIGURATION_ANALYSIS.md`
- Fix Status: `NETWORKMANAGER_FIX_STATUS.md`
