// import * as SecureStore from "expo-secure-store";

// const ACCESS_KEY = "edu_access_token";
// const REFRESH_KEY = "edu_refresh_token";

// export async function getAccessToken() {
//   return SecureStore.getItemAsync(ACCESS_KEY);
// }

// export async function getRefreshToken() {
//   return SecureStore.getItemAsync(REFRESH_KEY);
// }

// export async function setTokens(tokens: { access: string; refresh: string }) {
//   await SecureStore.setItemAsync(ACCESS_KEY, tokens.access);
//   await SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh);
// }

// export async function updateAccessToken(access: string) {
//   await SecureStore.setItemAsync(ACCESS_KEY, access);
// }

// export async function clearTokens() {
//   await SecureStore.deleteItemAsync(ACCESS_KEY);
//   await SecureStore.deleteItemAsync(REFRESH_KEY);
// }




import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const ACCESS_KEY = "edu_access_token";
const REFRESH_KEY = "edu_refresh_token";

const isWeb = Platform.OS === "web";

export async function getAccessToken() {
  if (isWeb) return localStorage.getItem(ACCESS_KEY);
  return SecureStore.getItemAsync(ACCESS_KEY);
}

export async function getRefreshToken() {
  if (isWeb) return localStorage.getItem(REFRESH_KEY);
  return SecureStore.getItemAsync(REFRESH_KEY);
}

export async function setTokens(tokens: { access: string; refresh: string }) {
  if (isWeb) {
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  } else {
    await SecureStore.setItemAsync(ACCESS_KEY, tokens.access);
    await SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh);
  }
}

export async function updateAccessToken(access: string) {
  if (isWeb) {
    localStorage.setItem(ACCESS_KEY, access);
  } else {
    await SecureStore.setItemAsync(ACCESS_KEY, access);
  }
}

export async function clearTokens() {
  if (isWeb) {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  } else {
    await SecureStore.deleteItemAsync(ACCESS_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  }
}
