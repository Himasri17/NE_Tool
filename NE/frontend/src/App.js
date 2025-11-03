import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"; 
import HomePage from "./pages/HomePage"; 
import Login from "./pages/User Authentication/Login";
import Register from "./pages/User Authentication/Register";
import Dashboard from "./pages/User/Dashboard"; 
import AdminDashboard from "./pages/Admin/AdminDashboard";
import ProjectSentencesReview from "./pages/Admin/ProjectSentencesReview"; 
import AdminApprovalList from "./pages/Admin/AdminApprovalList";
import AnalyticsDashboard from "./pages/Admin/AnalyticsDashboard"; 
import ForgotPassword from "./pages/User Authentication/ForgotPassword";
import ResetPassword from "./pages/User Authentication/ResetPassword";
import ReviewerDashboard from './pages/Reviewer/ReviewerDashboard';
import SentenceReviewPanel from './pages/Reviewer/SentenceReviewPanel';
import UserLogbook from "./pages/Admin/UserLogBook";
import DeveloperDashboard from './pages/Developer/DeveloperDashboard';

// --- Component to handle redirection based on stored role ---
const RoleRouter = () => {
    const userString = localStorage.getItem('user');
    const location = useLocation(); 

    if (!userString) {
        // Only redirect if we are not already on the login/register pages
        if (!location.pathname.includes('login') && !location.pathname.includes('register')) {
             return <Navigate to="/login" replace />;
        }
        return null; 
    }
    
    let user;
    try {
        user = JSON.parse(userString);
    } catch (e) {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        return <Navigate to="/login" replace />;
    }

    const role = user.role ? user.role.toLowerCase() : 'user';
    const username = user.username;

    if (!username) {
        return <Navigate to="/login" replace />;
    }

    // Determine the target path
    let targetPath;
    switch (role) {
        case 'developer':
            targetPath = `/developer/${username}`;
            break;
        case 'admin':
            targetPath = `/admin/${username}`;
            break;
        case 'reviewer':
            targetPath = `/reviewer/${username}`;
            break;
        case 'user': // Annotator/Default User
        default:
            targetPath = `/dashboard/${username}`;
            break;
    }
    
    // CRITICAL FIX: If the current path is NOT the target, navigate there.
    if (location.pathname !== targetPath) {
        return <Navigate to={targetPath} replace />;
    }

    // NEW FIX: If we ARE on the correct path, let the rendering proceed normally.
    // The component responsible for the view (e.g., DeveloperDashboard) will handle the rendering.
    return null; 
};


function App() {
    return (
        <BrowserRouter>
            <Routes>
                
                <Route path="/" element={<HomePage />} />
                
                {/* 2. Authentication Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />

                {/* 1. Universal Dashboard Entry Point: Redirects to correct dashboard */}
                <Route path="/home" element={<RoleRouter />} /> 

                {/* 3. User Dashboard Routes (Annotator/User) */}
                <Route path="/dashboard/:username" element={<Dashboard />} />
                
                {/* 4. Admin Dashboard Routes */}
                <Route path="/admin/:username" element={<AdminDashboard />} /> 
                <Route path="/admin/:username/logbook" element={<UserLogbook />} />
                <Route path="/admin/:username/approvals" element={<AdminApprovalList />} />
                <Route path="/admin/:username/analytics" element={<AnalyticsDashboard />} />
                <Route 
                    path="/admin/:username/project/:projectId/user/:targetUsername/sentences" 
                    element={<ProjectSentencesReview />} 
                />

                {/* 5. Reviewer Routes */}
                <Route path="/reviewer/:username" element={<ReviewerDashboard />} />
                <Route 
                    path="/reviewer/:username/project/:projectId/user/:targetUsername" 
                    element={<SentenceReviewPanel />} 
                />

                {/* 6. NEW Developer Route: Renders the Developer Dashboard component */}
                <Route path="/developer/:username" element={<DeveloperDashboard />} /> 

            </Routes>
        </BrowserRouter>
    );
}

export default App;