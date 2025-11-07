import React, { useState, useEffect} from 'react';
import { useParams } from 'react-router-dom';
import { 
    Container, Button, Typography, List, ListItem, Box, 
    Divider, CircularProgress, Paper, useTheme, Dialog, DialogTitle, 
    DialogContent, DialogActions, TextField, Alert, IconButton, Snackbar,
    Backdrop
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import CheckIcon from '@mui/icons-material/Check';
import CancelIcon from '@mui/icons-material/Cancel';
import RefreshIcon from '@mui/icons-material/Refresh';
import Navbar from '../../components/Navbar'; 
import { getToken } from '../../components/authUtils';

export default function AdminApprovalList() {
    const [pendingUsers, setPendingUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [rejectionReason, setRejectionReason] = useState('');
    const [actionInProgress, setActionInProgress] = useState(false); // Overall loading state
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
    const theme = useTheme();
    const { username } = useParams(); 
    
    // 1. Fetch unapproved users
    const fetchPendingUsers = async () => {
        setIsLoading(true);
        try {
            const token = getToken();
            if (!token) {
                throw new Error("No authentication token found. Please log in again.");
            }

            const res = await fetch("http://127.0.0.1:5001/admin/pending-users", {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!res.ok) {
                if (res.status === 401) {
                    throw new Error("Authentication failed. Please log in again.");
                }
                throw new Error("Failed to fetch pending users. Unauthorized or API error.");
            }
            
            const data = await res.json();
            setPendingUsers(data);
        } catch (error) {
            console.error("Fetch error:", error);
            showSnackbar(`Error fetching users: ${error.message}`, 'error');
            setPendingUsers([]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPendingUsers();
    }, []);

    // Snackbar helper
    const showSnackbar = (message, severity = 'success') => {
        setSnackbar({ open: true, message, severity });
    };

    const handleCloseSnackbar = () => {
        setSnackbar({ ...snackbar, open: false });
    };

    // 2. Approve user handler
    const handleApprove = async (userId, userEmail) => {
        const confirmApproval = window.confirm(`Are you sure you want to approve user: ${userEmail}?`);
        if (!confirmApproval) return;
        
        setActionInProgress(true); // Set overall loading state
        try {
            const token = getToken();
            
            const res = await fetch(`http://127.0.0.1:5001/admin/approve-user/${userId}`, { 
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    adminUsername: username
                })
            });
            
            if (res.ok) {
                setPendingUsers(prev => prev.filter(user => user._id !== userId));
                showSnackbar(`User ${userEmail} approved successfully!`, 'success');
            } else {
                if (res.status === 401) {
                    throw new Error("Authentication failed. Please log in again.");
                }
                const errorData = await res.json().catch(() => ({ message: 'Server failed to approve.' }));
                showSnackbar(`Approval failed: ${errorData.message}`, 'error');
            }
        } catch (error) {
            console.error("Approval API call failed:", error);
            showSnackbar(`Approval failed: ${error.message}`, 'error');
        } finally {
            setActionInProgress(false); // Clear overall loading state
        }
    };

    // 3. Reject user handlers
    const openRejectDialog = (user) => {
        setSelectedUser(user);
        setRejectionReason('');
        setRejectDialogOpen(true);
    };

    const closeRejectDialog = () => {
        setRejectDialogOpen(false);
        setSelectedUser(null);
        setRejectionReason('');
    };

    const handleReject = async () => {
        if (!selectedUser) return;
        
        setActionInProgress(true); // Set overall loading state
        try {
            const token = getToken();
            
            const res = await fetch(`http://127.0.0.1:5001/admin/reject-user/${selectedUser._id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    adminUsername: username,
                    rejectionReason: rejectionReason || 'No reason provided'
                })
            });
            
            if (res.ok) {
                setPendingUsers(prev => prev.filter(user => user._id !== selectedUser._id));
                showSnackbar(`User ${selectedUser.email} rejected successfully!`, 'success');
                closeRejectDialog();
            } else {
                if (res.status === 401) {
                    throw new Error("Authentication failed. Please log in again.");
                }
                const errorData = await res.json().catch(() => ({ message: 'Server failed to reject.' }));
                showSnackbar(`Rejection failed: ${errorData.message}`, 'error');
            }
        } catch (error) {
            console.error("Rejection API call failed:", error);
            showSnackbar(`Rejection failed: ${error.message}`, 'error');
        } finally {
            setActionInProgress(false); // Clear overall loading state
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', width: '100vw', overflow: 'hidden' }}>
            <Navbar username={username} />
            
            {/* Overall Loading Backdrop */}
            <Backdrop
                sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
                open={actionInProgress}
            >
                <Box sx={{ textAlign: 'center' }}>
                    <CircularProgress color="inherit" />
                    <Typography variant="h6" sx={{ mt: 2 }}>
                        Processing action...
                    </Typography>
                </Box>
            </Backdrop>

            <Container maxWidth="md" sx={{ mt: 5 }}>
                <Paper elevation={4} sx={{ p: 4 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h4" color="primary.main" fontWeight="bold">
                            Pending User Approvals
                        </Typography>
                        <Button 
                            variant="outlined" 
                            onClick={fetchPendingUsers}
                            disabled={isLoading || actionInProgress}
                            startIcon={isLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
                        >
                            {isLoading ? 'Refreshing...' : 'Refresh'}
                        </Button>
                    </Box>
                    
                    <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 2 }}>
                        Review new registrations and grant access to the platform.
                    </Typography>
                    <Divider sx={{ mb: 3 }} />

                    {isLoading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                            <CircularProgress />
                        </Box>
                    ) : pendingUsers.length === 0 ? (
                        <Box sx={{ p: 3, textAlign: 'center' }}>
                            <Typography variant="h6" color="success.main">
                                No users currently awaiting approval. ✅
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                All registration requests have been processed.
                            </Typography>
                        </Box>
                    ) : (
                        <Paper variant="outlined">
                            <List disablePadding>
                                {pendingUsers.map(user => (
                                    <ListItem
                                        key={user._id}
                                        secondaryAction={
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                <Button 
                                                    variant="contained" 
                                                    color="success"
                                                    startIcon={<CheckIcon />}
                                                    onClick={() => handleApprove(user._id, user.email)}
                                                    disabled={actionInProgress}
                                                    size="small"
                                                >
                                                    Approve
                                                </Button>
                                                <Button 
                                                    variant="outlined" 
                                                    color="error"
                                                    startIcon={<CancelIcon />}
                                                    onClick={() => openRejectDialog(user)}
                                                    disabled={actionInProgress}
                                                    size="small"
                                                >
                                                    Reject
                                                </Button>
                                            </Box>
                                        }
                                        sx={{ 
                                            borderBottom: `1px solid ${theme.palette.grey[200]}`,
                                            '&:last-child': { borderBottom: 'none' },
                                            py: 2
                                        }}
                                    >
                                        <Box sx={{ flex: 1 }}>
                                            <Typography variant="h6" fontWeight="bold" gutterBottom>
                                                {user.full_name || user.username}
                                            </Typography>
                                            <Box component="div" sx={{ mt: 1 }}>
                                                <Typography variant="body2" component="div">
                                                    <strong>Email:</strong> {user.email}
                                                </Typography>
                                                <Typography variant="body2" component="div">
                                                    <strong>Role:</strong> {user.role}
                                                </Typography>
                                                <Typography variant="body2" component="div">
                                                    <strong>Organization:</strong> {user.organization}
                                                </Typography>
                                                <Typography variant="body2" component="div">
                                                    <strong>Languages:</strong> {Array.isArray(user.languages) ? user.languages.join(', ') : (user.languages || 'N/A')}
                                                </Typography>
                                                <Typography variant="body2" color="text.secondary" component="div">
                                                    <strong>Registered:</strong> {user.registered_at}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </ListItem>
                                ))}
                            </List>
                        </Paper>
                    )}
                </Paper>

                {/* Rejection Dialog */}
                <Dialog open={rejectDialogOpen} onClose={closeRejectDialog} maxWidth="sm" fullWidth>
                    <DialogTitle>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="h6">Reject User Registration</Typography>
                            <IconButton onClick={closeRejectDialog} size="small" disabled={actionInProgress}>
                                <CloseIcon />
                            </IconButton>
                        </Box>
                    </DialogTitle>
                    <DialogContent>
                        <Alert severity="warning" sx={{ mb: 2 }}>
                            You are about to reject {selectedUser?.full_name || selectedUser?.email}'s registration request.
                        </Alert>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            Please provide a reason for rejection (optional):
                        </Typography>
                        <TextField
                            fullWidth
                            multiline
                            rows={3}
                            placeholder="Enter rejection reason..."
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                            variant="outlined"
                            disabled={actionInProgress}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={closeRejectDialog} disabled={actionInProgress}>
                            Cancel
                        </Button>
                        <Button 
                            onClick={handleReject} 
                            color="error" 
                            variant="contained"
                            disabled={actionInProgress}
                            startIcon={<CancelIcon />}
                        >
                            Reject User
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Snackbar for notifications */}
                <Snackbar
                    open={snackbar.open}
                    autoHideDuration={6000}
                    onClose={handleCloseSnackbar}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                >
                    <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
                        {snackbar.message}
                    </Alert>
                </Snackbar>
            </Container>
        </Box>
    );
}