import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { apiRequest } from "./api";

// Show notifications while the app is foregrounded.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

/**
 * Ask for permission, obtain the Expo push token, and register it with the
 * backend (`POST /api/notifications/devices/`). Fire-and-forget: returns null
 * on any failure so callers never break the auth flow.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  try {
    let { status } = await Notifications.getPermissionsAsync();
    if (status !== "granted") {
      status = (await Notifications.requestPermissionsAsync()).status;
    }
    if (status !== "granted") return null;

    const { data: token } = await Notifications.getExpoPushTokenAsync();
    if (!token) return null;

    await apiRequest("/api/notifications/devices/", {
      method: "POST",
      body: { token, platform: Platform.OS },
    });
    return token;
  } catch {
    return null;
  }
}
