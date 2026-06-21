# EduPlatform Mobile

Expo React Native app for the EduPlatform backend.

## Run

```bash
cd mobile
npm install
npm run start
```

Set `EXPO_PUBLIC_API_BASE_URL` if the Django backend is not reachable at `http://127.0.0.1:8000`.

## Google sign in

Create OAuth client IDs in Google Cloud and set these in `mobile/.env`:

```bash
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=your-web-client-id.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID=your-expo-client-id.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=your-android-client-id.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=your-ios-client-id.apps.googleusercontent.com
```

The Django backend must include the same IDs in `GOOGLE_OAUTH_CLIENT_IDS`, comma-separated.

For Android emulator use:

```bash
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000
```

For a physical phone, use your computer's LAN IP address.
