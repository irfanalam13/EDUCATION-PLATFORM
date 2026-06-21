import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
 
import { LoadingView } from "@/components/StateView";
import { Text } from "@/components/Text";
import { useAuth } from "@/providers/AuthProvider";
import { palette } from "@/theme";
import type { AppRoute, AuthRoute } from "./routes";
import { LoginScreen } from "@/screens/auth/LoginScreen";
import { SignupScreen } from "@/screens/auth/SignupScreen";
import { AiScreen } from "@/screens/main/AiScreen";
import { AnalyticsScreen } from "@/screens/main/AnalyticsScreen";
import { AssistantScreen } from "@/screens/main/AssistantScreen";
import { DashboardScreen } from "@/screens/main/DashboardScreen";
import { LearnScreen } from "@/screens/main/LearnScreen";
import { NotesScreen } from "@/screens/main/NotesScreen";
import { QuizScreen } from "@/screens/main/QuizScreen";

const tabs: Array<{ route: AppRoute; label: string; icon: keyof typeof Ionicons.glyphMap }> = [
  { route: "dashboard", label: "Home", icon: "home-outline" },
  { route: "learn", label: "Learn", icon: "book-outline" },
  { route: "notes", label: "Notes", icon: "create-outline" },
  { route: "quiz", label: "Quiz", icon: "checkmark-circle-outline" },
  { route: "ai", label: "Coach", icon: "bulb-outline" },
  { route: "assistant", label: "Chat", icon: "sparkles-outline" }
];

export function RootNavigator({ bootstrapping }: { bootstrapping: boolean }) {
  const { user, role } = useAuth();
  const [authRoute, setAuthRoute] = useState<AuthRoute>("login");
  const [appRoute, setAppRoute] = useState<AppRoute>("dashboard");

  // Analytics is an institution-staff feature; only surface it to non-students.
  const visibleTabs =
    role && role !== "STUDENT"
      ? [...tabs, { route: "analytics" as AppRoute, label: "Insights", icon: "stats-chart-outline" as const }]
      : tabs;

  if (bootstrapping) {
    return (
      <View style={styles.loading}>
        <LoadingView label="Preparing your learning workspace..." />
      </View>
    );
  }

  if (!user) {
    return authRoute === "login" ? (
      <LoginScreen onGoSignup={() => setAuthRoute("signup")} />
    ) : (
      <SignupScreen onGoLogin={() => setAuthRoute("login")} />
    );
  }

  return (
    <View style={styles.app}>
      <View style={styles.content}>
        {appRoute === "dashboard" ? <DashboardScreen /> : null}
        {appRoute === "learn" ? <LearnScreen onOpenQuiz={() => setAppRoute("quiz")} /> : null}
        {appRoute === "notes" ? <NotesScreen /> : null}
        {appRoute === "quiz" ? <QuizScreen /> : null}
        {appRoute === "ai" ? <AiScreen /> : null}
        {appRoute === "assistant" ? <AssistantScreen /> : null}
        {appRoute === "analytics" ? <AnalyticsScreen /> : null}
      </View>

      <View style={styles.tabBar}>
        {visibleTabs.map((tab) => {
          const active = tab.route === appRoute;
          return (
            <Pressable key={tab.route} style={styles.tab} onPress={() => setAppRoute(tab.route)}>
              <Ionicons name={tab.icon} size={22} color={active ? palette.primary : palette.muted} />
              <Text style={[styles.tabText, active ? styles.tabTextActive : null]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  app: {
    flex: 1,
    backgroundColor: palette.background
  },
  content: {
    flex: 1
  },
  loading: {
    flex: 1,
    backgroundColor: palette.background,
    justifyContent: "center",
    padding: 16
  },
  tabBar: {
    backgroundColor: palette.card,
    borderColor: palette.border,
    borderTopWidth: 1,
    flexDirection: "row",
    paddingBottom: 6,
    paddingTop: 8
  },
  tab: {
    alignItems: "center",
    flex: 1,
    gap: 2
  },
  tabText: {
    color: palette.muted,
    fontSize: 11,
    fontWeight: "700"
  },
  tabTextActive: {
    color: palette.primary
  }
});
