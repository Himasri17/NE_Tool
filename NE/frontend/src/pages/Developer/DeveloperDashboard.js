import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { 
    Container, Typography, Box, Paper, Button, CircularProgress, Alert, Divider, 
    List, ListItem, ListItemText, ListItemIcon, ListItemSecondaryAction, IconButton, Badge, 
    Dialog, DialogTitle, DialogContent, DialogActions, TextField, useTheme, Drawer 
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import FeedbackIcon from '@mui/icons-material/Feedback';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import MenuIcon from '@mui/icons-material/Menu';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import { red } from '@mui/material/colors'; // Import specific color palette for safety
import { removeToken } from '../../components/authUtils';

const API_BASE_URL = 'http://127.0.0.1:5001';

// --- Integrated Navbar Component (Specialized for Developer Role) ---
const DeveloperNavbar = ({
    username,
    pendingApprovalsCount,
    unreviewedFeedbacksCount,
    onOpenFeedbackDialog
}) => {
    const navigate = useNavigate();
    const location = useLocation();
    const theme = useTheme();
    const [drawerOpen, setDrawerOpen] = useState(false);
    
    // --- NAVBAR COLOR DEFINITION ---
    // Change this hex code to modify the Navbar color easily.
    const DEVELOPER_NAV_COLOR = '#1D2B3F'; 

    const totalNotificationCount = pendingApprovalsCount + unreviewedFeedbacksCount;

    const navItems = [
        { 
            name: 'APPROVE ADMINS', 
            path: `/developer/${username}`, 
            icon: GroupAddIcon,
            badge: pendingApprovalsCount, 
        },
        { 
            name: 'VIEW FEEDBACKS', 
            path: null, 
            action: onOpenFeedbackDialog, 
            badge: unreviewedFeedbacksCount, 
            icon: FeedbackIcon 
        },
    ];
    
    const isPathActive = (path) => {
        return location.pathname === path || location.pathname === `${path}/`;
    };

    const handleNavigation = (path, action) => {
        setDrawerOpen(false); 
        if (path) {
            navigate(path);
        } else if (action) {
            action();
        }
    };
    
    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        removeToken();
        navigate('/login');
    };

    return (
        <Box sx={{ 
            display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
            height: '60px', 
            bgcolor: DEVELOPER_NAV_COLOR, // NAVBAR BACKGROUND COLOR
            color: 'white', 
            p: 2, width: '100%', boxSizing: 'border-box', flexShrink: 0 
        }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <IconButton color="inherit" aria-label="open drawer" onClick={() => setDrawerOpen(true)} edge="start" sx={{ mr: 2 }}>
                    <Badge badgeContent={totalNotificationCount} color="error" overlap="circular" max={99}>
                        <MenuIcon /> 
                    </Badge>
                </IconButton>
                <Typography variant="h6" fontWeight={500} sx={{ display: { xs: 'none', sm: 'block' } }}>
                    System Developer Workbench
                </Typography>
                <DeveloperModeIcon sx={{ ml: 1 }}/>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 2, flexShrink: 0 }}>
                <Typography variant="body1" sx={{ color: 'white', fontWeight: 'bold', mr: 1 }}>
                    Dev: {username}
                </Typography>
                <Button 
                    variant="outlined" size="small" 
                    sx={{ color: 'white', borderColor: 'white' }} 
                    onClick={handleLogout}
                >
                    LOG OUT
                </Button>
            </Box>

            <Drawer
                anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}
                PaperProps={{ sx: { width: 250, bgcolor: theme.palette.background.paper } }}
            >
                <Box sx={{ p: 2, bgcolor: DEVELOPER_NAV_COLOR, color: 'white' }}>
                    <Typography variant="h6" fontWeight="bold">Developer Menu</Typography>
                </Box>
                <Divider />
                <List>
                    {navItems.map((item) => {
                        const isActive = item.path ? isPathActive(item.path) : false;
                        const ButtonIcon = item.icon;

                        return (
                            <ListItem 
                                key={item.name} 
                                button 
                                onClick={() => handleNavigation(item.path, item.action)}
                                sx={{ bgcolor: isActive ? theme.palette.action.selected : 'transparent', '&:hover': { bgcolor: theme.palette.action.hover } }}
                            >
                                <ListItemIcon>
                                    <Badge 
                                        badgeContent={item.badge} 
                                        color={item.name.includes('APPROVE') ? 'error' : 'warning'} 
                                        overlap="circular" max={99}
                                    >
                                        {/* Using theme.palette.text.secondary for consistency with non-active text color */}
                                        {ButtonIcon && <ButtonIcon sx={{ color: isActive ? theme.palette.secondary.main : theme.palette.text.secondary }} />}
                                    </Badge>
                                </ListItemIcon>
                                <ListItemText 
                                    primary={item.name} 
                                    primaryTypographyProps={{ 
                                        fontWeight: isActive ? 'bold' : 'normal',
                                        color: isActive ? theme.palette.secondary.main : theme.palette.text.primary
                                    }} 
                                />
                            </ListItem>
                        );
                    })}
                </List>
            </Drawer>
        </Box>
    );
};

// --- Helper Component: Feedback Viewing Modal ---
const FeedbackViewer = ({ open, onClose, feedbacks, onMarkReviewed, onDeleteFeedback, apiBaseUrl, authHeaders }) => {
    const theme = useTheme();

    const handleViewFile = (filePath) => {
        window.open(`${apiBaseUrl}/feedback_uploads/${filePath}`, '_blank');
    };
    
    const handleMarkReviewedLocal = async (feedbackId) => {
        try {
            const response = await fetch(`${apiBaseUrl}/developer/feedbacks/${feedbackId}/review`, { 
                method: 'PUT',
                headers: authHeaders
            });
            if (response.ok) {
                onMarkReviewed(feedbackId); 
            } else {
                 alert("Failed to mark as reviewed.");
            }
        } catch (e) {
            alert("Network Error marking feedback reviewed.");
        }
    };
    
    const handleDeleteFeedbackLocal = async (feedbackId) => {
        if (!window.confirm("Are you sure you want to delete this feedback and any associated file?")) return;
        try {
            const response = await fetch(`${apiBaseUrl}/developer/feedbacks/${feedbackId}`, { 
                method: 'DELETE',
                headers: authHeaders
            });
            if (response.ok) {
                onDeleteFeedback(feedbackId); 
            } else {
                 alert("Failed to delete feedback.");
            }
        } catch (e) {
            alert("Network Error deleting feedback.");
        }
    };


    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle sx={{ bgcolor: '#1D2B3F', color: 'white' }}>
                <FeedbackIcon sx={{ mr: 1, verticalAlign: 'middle' }} /> All User Feedbacks
            </DialogTitle>
            <DialogContent dividers>
                <List>
                    {feedbacks.length === 0 ? (
                        <ListItem><ListItemText primary="No user feedback submitted yet." /></ListItem>
                    ) : (
                        feedbacks.map((feedback) => (
                            <ListItem 
                                key={feedback.id} 
                                divider 
                                // FIX: Use standard color from palette for safety
                                sx={{ bgcolor: feedback.is_reviewed ? theme.palette.grey[50] : red[50] }}
                            >
                                <ListItemText 
                                    primary={`[${feedback.is_reviewed ? 'REVIEWED' : 'PENDING'}] From: ${feedback.email}`}
                                    secondary={
                                        <React.Fragment>
                                            <Typography component="span" variant="body2" color="text.primary">
                                                {feedback.feedback_text}
                                            </Typography>
                                            <br />
                                            <Typography variant="caption" color="text.secondary">
                                                Submitted: {feedback.time} | File: {feedback.file_path === 'None' ? 'N/A' : feedback.file_path}
                                            </Typography>
                                        </React.Fragment>
                                    }
                                    primaryTypographyProps={{ fontWeight: feedback.is_reviewed ? 'normal' : 'bold' }}
                                />
                                <ListItemSecondaryAction>
                                    {feedback.file_path !== 'None' && (
                                        <IconButton edge="end" aria-label="view-file" onClick={() => handleViewFile(feedback.file_path)} sx={{ mr: 1 }}>
                                            <VisibilityIcon color="primary" />
                                        </IconButton>
                                    )}
                                    <IconButton edge="end" aria-label="delete" color="error" onClick={() => handleDeleteFeedbackLocal(feedback.id)} sx={{ mr: 1 }}>
                                        <DeleteIcon />
                                    </IconButton>
                                    {!feedback.is_reviewed && (
                                        <Button 
                                            variant="contained" color="success" size="small"
                                            onClick={() => handleMarkReviewedLocal(feedback.id)}
                                        >
                                            Mark Reviewed
                                        </Button>
                                    )}
                                </ListItemSecondaryAction>
                            </ListItem>
                        ))
                    )}
                </List>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} color="primary">Close</Button>
            </DialogActions>
        </Dialog>
    );
};

// --- MAIN DEVELOPER DASHBOARD COMPONENT ---

export default function DeveloperDashboard() {
    const { username } = useParams();
    const [pendingUsers, setPendingUsers] = useState([]);
    const [feedbacks, setFeedbacks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isFeedbackViewerOpen, setIsFeedbackViewerOpen] = useState(false);
    const [rejectionReason, setRejectionReason] = useState('');
    const [rejectingUserId, setRejectingUserId] = useState(null);

    const getAuthHeaders = useCallback(() => {
        const token = localStorage.getItem('jwt_token') || localStorage.getItem('token');
        console.log('DEBUG - Using token:', token ? 'Token found' : 'No token found');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        };
    }, []);

    // --- Fetch Data (Pending Users and Feedback) ---
    const fetchDashboardData = useCallback(async () => {
        setLoading(true);
        setError('');
        
        try {
            const headers = getAuthHeaders();
            
            // 1. Fetch Pending Admins (Admins and Developers awaiting approval)
            const usersResponse = await fetch(`${API_BASE_URL}/developer/pending-users`, { headers });
            const usersData = await usersResponse.json();

            if (usersResponse.ok) {
                setPendingUsers(usersData.pending_users || []);
            } else {
                // If 401/403, throw custom error to catch block
                if (usersResponse.status === 401 || usersResponse.status === 403) {
                     throw new Error(`Auth Error: ${usersResponse.status} - ${usersData.message || 'Unauthorized'}`);
                }
                throw new Error(usersData.message || "Failed to fetch pending users.");
            }

            // 2. Fetch Feedback
            const feedbackResponse = await fetch(`${API_BASE_URL}/developer/feedbacks`, { headers });
            const feedbackData = await feedbackResponse.json();

            if (feedbackResponse.ok) {
                setFeedbacks(feedbackData.feedbacks || []);
            } else {
                 if (feedbackResponse.status === 401 || feedbackResponse.status === 403) {
                     throw new Error(`Auth Error: ${feedbackResponse.status} - ${feedbackData.message || 'Unauthorized'}`);
                }
                throw new Error(feedbackData.message || "Failed to fetch feedback.");
            }

        } catch (err) {
            console.error("Dashboard Fetch Error:", err);
            // Handle the specific error shown in the screenshot
            if (err.message.includes('Failed to fetch') && !err.message.includes('Auth Error')) {
                 setError(`Network connection failed. Ensure the Flask backend is running at ${API_BASE_URL}.`);
            } else if (err.message.includes('Auth Error')) {
                 setError("Authorization failed. Please log in again to refresh your developer session.");
            } else {
                setError(`Error loading dashboard data. Details: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    useEffect(() => {
        fetchDashboardData();
    }, [username, fetchDashboardData]);

    // --- Approval/Rejection Handler ---
    const handleApproval = async (userId, action) => {
        if (action === 'reject') {
            setRejectingUserId(userId);
            return; 
        }

        setLoading(true);
        setError('');
        
        try {
            const response = await fetch(`${API_BASE_URL}/developer/approve-user/${userId}`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ action, approved_by: username }),
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message);
                fetchDashboardData(); 
            } else {
                setError(data.message || `Failed to ${action} user.`);
            }

        } catch (err) {
            setError("Network error during approval process.");
        } finally {
            if (action !== 'reject') setLoading(false); 
        }
    };

    // --- Confirmation Handler for Rejection Modal ---
    const handleRejectionConfirmation = async () => {
        const userId = rejectingUserId;
        if (!rejectionReason.trim()) {
            alert("Rejection reason is required.");
            return;
        }

        setRejectingUserId(null); 
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE_URL}/developer/approve-user/${userId}`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ 
                    action: 'reject', 
                    approved_by: username, 
                    rejectionReason: rejectionReason 
                }),
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message);
                fetchDashboardData(); 
            } else {
                setError(data.message || `Failed to reject user.`);
            }

        } catch (err) {
            setError("Network error during rejection process.");
        } finally {
            setLoading(false);
            setRejectionReason('');
        }
    };
    
    // --- Feedback Handlers to update state ---
    const handleMarkReviewed = (feedbackId) => {
        fetchDashboardData();
    };
    
    const handleDeleteFeedback = (feedbackId) => {
        fetchDashboardData();
    };


    // --- Render Logic ---
    const pendingAdminsCount = pendingUsers.length;
    const unreviewedFeedbacksCount = feedbacks.filter(f => !f.is_reviewed).length;
    const authDetails = getAuthHeaders();

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <DeveloperNavbar
                username={username}
                pendingApprovalsCount={pendingAdminsCount}
                unreviewedFeedbacksCount={unreviewedFeedbacksCount}
                onOpenFeedbackDialog={() => setIsFeedbackViewerOpen(true)}
            />

            <Container component="main" maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
                    <DeveloperModeIcon sx={{ mr: 1, verticalAlign: 'middle' }} /> System Developer Dashboard
                </Typography>
                <Divider sx={{ mb: 3 }} />

                {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', pt: 5 }}><CircularProgress /></Box>
                )}

                {!loading && (
                    <React.Fragment>
                        {/* --- Admin/Developer Approval Section --- */}
                        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
                            <Typography variant="h6" gutterBottom>
                                <PersonAddIcon sx={{ mr: 1, verticalAlign: 'middle' }} /> Pending Registrations (Admins)
                            </Typography>
                            <Divider sx={{ mb: 2 }} />
                            <List>
                                {pendingUsers.length === 0 ? (
                                    <ListItem><ListItemText primary="No Admin or Developer registrations currently awaiting approval." /></ListItem>
                                ) : (
                                    pendingUsers.map((user) => (
                                        <ListItem key={user._id} divider>
                                            <ListItemText 
                                                primary={`[${user.role.toUpperCase()}] ${user.full_name} (${user.email})`}
                                                secondary={`Organization: ${user.organization} | Registered: ${user.registered_at}`}
                                            />
                                            <ListItemSecondaryAction>
                                                <Button 
                                                    size="small" variant="contained" color="success" 
                                                    onClick={() => handleApproval(user._id, 'approve')}
                                                    sx={{ mr: 1 }}
                                                >
                                                    <CheckCircleIcon sx={{ mr: 0.5 }} /> Approve
                                                </Button>
                                                <Button
                                                    size="small" variant="contained" color="error" 
                                                    onClick={() => handleApproval(user._id, 'reject')}
                                                >
                                                    <CancelIcon sx={{ mr: 0.5 }} /> Reject
                                                </Button>
                                            </ListItemSecondaryAction>
                                        </ListItem>
                                    ))
                                )}
                            </List>
                        </Paper>
                        
                        {/* Status Card for Feedback Visibility (Quick check for developer) */}
                        <Paper elevation={3} sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>
                                <FeedbackIcon sx={{ mr: 1, verticalAlign: 'middle' }} /> Feedback Summary
                            </Typography>
                            <Divider sx={{ mb: 2 }} />
                            <Typography variant="body1">
                                Total Feedbacks: **{feedbacks.length}**
                            </Typography>
                            <Typography variant="body1" color={unreviewedFeedbacksCount > 0 ? 'error' : 'text.secondary'} sx={{ mb: 2 }}>
                                Unreviewed: **{unreviewedFeedbacksCount}**
                            </Typography>
                            <Button 
                                variant="contained" 
                                color="secondary" 
                                onClick={() => setIsFeedbackViewerOpen(true)}
                            >
                                Open Feedback Viewer
                            </Button>
                        </Paper>
                    </React.Fragment>
                )}
            </Container>
            
            {/* --- Feedback Viewer Dialog --- */}
            <FeedbackViewer 
                open={isFeedbackViewerOpen} 
                onClose={() => setIsFeedbackViewerOpen(false)}
                feedbacks={feedbacks}
                onMarkReviewed={handleMarkReviewed}
                onDeleteFeedback={handleDeleteFeedback}
                apiBaseUrl={API_BASE_URL}
                authHeaders={authDetails}
            />

            {/* --- Rejection Reason Modal --- */}
            <Dialog 
                open={rejectingUserId !== null} 
                onClose={() => setRejectingUserId(null)}
            >
                <DialogTitle>Provide Rejection Reason</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Reason for Rejection"
                        type="text"
                        fullWidth
                        multiline
                        rows={4}
                        variant="outlined"
                        value={rejectionReason}
                        onChange={(e) => setRejectionReason(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => {setRejectingUserId(null); setRejectionReason('');}} color="error">Cancel</Button>
                    <Button onClick={handleRejectionConfirmation} color="primary" variant="contained" disabled={!rejectionReason.trim()}>Confirm Reject</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
