// App Navigator — Main Navigation Structure
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { typography } from '../theme';

// Auth Screens
import HomeScreen from '../screens/auth/HomeScreen';
import LoginScreen from '../screens/auth/LoginScreen';
import SignupScreen from '../screens/auth/SignupScreen';

// Dashboard Screens
import AdminDashboard from '../screens/dashboard/AdminDashboard';
import AdminApprovals from '../screens/dashboard/AdminApprovals';
import DoctorDashboard from '../screens/dashboard/DoctorDashboard';
import ASHAInterface from '../screens/dashboard/ASHAInterface';

// Postnatal Screens
import PostnatalDashboard from '../screens/postnatal/PostnatalDashboard';
import ChildrenList from '../screens/postnatal/ChildrenList';
import GrowthCharts from '../screens/postnatal/GrowthCharts';
import VaccinationCalendar from '../screens/postnatal/VaccinationCalendar';
import MilestonesTracker from '../screens/postnatal/MilestonesTracker';
import PostnatalAssessments from '../screens/postnatal/PostnatalAssessments';
import AssessmentHistory from '../screens/postnatal/AssessmentHistory';
import MothersList from '../screens/postnatal/MothersList';

// Other Screens
import AIChatScreen from '../screens/chat/AIChatScreen';
import EmergencyScreen from '../screens/EmergencyScreen';
import ProfileScreen from '../screens/ProfileScreen';
import NotificationsScreen from '../screens/NotificationsScreen';

import { LoadingSpinner } from '../components/shared';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const PostnatalStack = createNativeStackNavigator();
const AdminStack = createNativeStackNavigator();

// --- Postnatal Stack ---
function PostnatalNavigator() {
    const { theme } = useTheme();
    return (
        <PostnatalStack.Navigator
            screenOptions={{
                headerStyle: { backgroundColor: theme.surface },
                headerTintColor: theme.text,
                headerTitleStyle: { fontWeight: '600' },
            }}
        >
            <PostnatalStack.Screen name="PostnatalDashboard" component={PostnatalDashboard} options={{ title: 'Postnatal Care', headerShown: false }} />
            <PostnatalStack.Screen name="ChildrenList" component={ChildrenList} options={{ title: 'Children' }} />
            <PostnatalStack.Screen name="MothersList" component={MothersList} options={{ title: 'Mothers' }} />
            <PostnatalStack.Screen name="GrowthCharts" component={GrowthCharts} options={{ title: 'Growth Charts' }} />
            <PostnatalStack.Screen name="VaccinationCalendar" component={VaccinationCalendar} options={{ title: 'Vaccinations' }} />
            <PostnatalStack.Screen name="MilestonesTracker" component={MilestonesTracker} options={{ title: 'Milestones' }} />
            <PostnatalStack.Screen name="PostnatalAssessments" component={PostnatalAssessments} options={{ title: 'Assessments' }} />
            <PostnatalStack.Screen name="AssessmentHistory" component={AssessmentHistory} options={{ title: 'Assessment History' }} />
        </PostnatalStack.Navigator>
    );
}

// --- Resolve dashboard based on role ---
function DashboardForRole() {
    const { user } = useAuth();
    if (user?.role === 'ADMIN') return <AdminDashboard />;
    // Both DOCTOR and ASHA_WORKER use the same DoctorDashboard (Prenatal Care)
    if (user?.role === 'DOCTOR' || user?.role === 'ASHA_WORKER') return <DoctorDashboard />;
    return <ASHAInterface />;
}

// --- Admin Stack (dashboard + approvals) ---
function AdminNavigator() {
    const { theme } = useTheme();
    return (
        <AdminStack.Navigator
            screenOptions={{
                headerStyle: { backgroundColor: theme.surface },
                headerTintColor: theme.text,
            }}
        >
            <AdminStack.Screen name="DashboardHome" component={DashboardForRole} options={{ headerShown: false }} />
            <AdminStack.Screen name="AdminApprovals" component={AdminApprovals} options={{ headerShown: false }} />
            <AdminStack.Screen name="MothersList" component={MothersList} options={{ title: 'Mothers' }} />
            <AdminStack.Screen name="ChildrenList" component={ChildrenList} options={{ title: 'Children' }} />
            <AdminStack.Screen name="PostnatalDashboard" component={PostnatalDashboard} options={{ title: 'Postnatal Care' }} />
            {/* Postnatal sub-screens accessible from ASHA/Doctor dashboard */}
            <AdminStack.Screen name="VaccinationCalendar" component={VaccinationCalendar} options={{ title: 'Vaccinations' }} />
            <AdminStack.Screen name="GrowthCharts" component={GrowthCharts} options={{ title: 'Growth Charts' }} />
            <AdminStack.Screen name="MilestonesTracker" component={MilestonesTracker} options={{ title: 'Milestones' }} />
            <AdminStack.Screen name="PostnatalAssessments" component={PostnatalAssessments} options={{ title: 'Assessments' }} />
            <AdminStack.Screen name="AssessmentHistory" component={AssessmentHistory} options={{ title: 'Assessment History' }} />
        </AdminStack.Navigator>
    );
}

// --- Main Tabs ---
function MainTabs() {
    const { t } = useTranslation();
    const { theme } = useTheme();

    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                headerShown: false,
                tabBarStyle: {
                    backgroundColor: theme.tabBar,
                    borderTopColor: theme.tabBarBorder,
                    height: 85,
                    paddingBottom: 25,
                    paddingTop: 8,
                },
                tabBarActiveTintColor: theme.primary,
                tabBarInactiveTintColor: theme.textTertiary,
                tabBarLabelStyle: typography.tabLabel,
                tabBarIcon: ({ focused, color, size }) => {
                    const icons = {
                        Dashboard: focused ? 'grid' : 'grid-outline',
                        Notifications: focused ? 'notifications' : 'notifications-outline',
                        Postnatal: focused ? 'heart' : 'heart-outline',
                        Emergency: focused ? 'warning' : 'warning-outline',
                        Profile: focused ? 'person' : 'person-outline',
                    };
                    return <Ionicons name={icons[route.name]} size={22} color={color} />;
                },
            })}
        >
            <Tab.Screen name="Dashboard" component={AdminNavigator} options={{ tabBarLabel: t('dashboard') }} />
            <Tab.Screen name="Notifications" component={NotificationsScreen} options={{ tabBarLabel: 'Alerts' }} />
            <Tab.Screen name="Postnatal" component={PostnatalNavigator} options={{ tabBarLabel: t('postnatal') }} />
            <Tab.Screen name="Emergency" component={EmergencyScreen} options={{ tabBarLabel: t('emergency') }} />
            <Tab.Screen name="Profile" component={ProfileScreen} options={{ tabBarLabel: t('profile') }} />
        </Tab.Navigator>
    );
}

// --- Root Navigator ---
export default function AppNavigator() {
    const { user, loading } = useAuth();

    if (loading) return <LoadingSpinner message="Loading Aanchal AI..." />;

    return (
        <NavigationContainer>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
                {user ? (
                    <Stack.Screen name="Main" component={MainTabs} />
                ) : (
                    <>
                        <Stack.Screen name="Home" component={HomeScreen} />
                        <Stack.Screen name="Login" component={LoginScreen} />
                        <Stack.Screen name="Signup" component={SignupScreen} />
                    </>
                )}
            </Stack.Navigator>
        </NavigationContainer>
    );
}
