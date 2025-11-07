// AssignUsersDialog.js
import React, { useState, useEffect } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    Button, FormControl, InputLabel, Select, MenuItem,
    Chip, Box, Typography, CircularProgress, Alert
} from '@mui/material';
import { getAuthHeaders } from '../../components/authUtils';    

export default function AssignUsersDialog({ open, onClose, projectId, projectName, adminUsername, projectLanguage }) {
    const [availableUsers, setAvailableUsers] = useState([]);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');

    // Fetch available users - UPDATED to filter by language
    const fetchAvailableUsers = async () => {
        setIsLoading(true);
        try {
            let url = 'http://127.0.0.1:5001/api/users-list';
            
            // If project language is available, filter by language
            if (projectLanguage) {
                url = `http://127.0.0.1:5001/api/users-by-language?language=${encodeURIComponent(projectLanguage)}`;
            }
            
            const response = await fetch(url, {
                headers: getAuthHeaders()
            });
            
            if (response.ok) {
                const users = await response.json();
                setAvailableUsers(users);
            } else {
                setError('Failed to fetch users list');
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            setError('Error fetching users list');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            fetchAvailableUsers();
            setSelectedUsers([]);
            setError('');
        }
    }, [open, projectLanguage]); // Added projectLanguage as dependency

    const handleAssignUsers = async () => {
        if (selectedUsers.length === 0) {
            setError('Please select at least one user');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            const response = await fetch(`http://127.0.0.1:5001/api/projects/${projectId}/assign_user`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    users: selectedUsers,
                    adminUsername: adminUsername
                })
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Success: ${result.message}`);
                onClose(true); // Pass true to indicate success
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to assign users');
            }
        } catch (error) {
            console.error('Error assigning users:', error);
            setError('Network error while assigning users');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = (success = false) => {
        setSelectedUsers([]);
        setError('');
        onClose(success);
    };

    return (
        <Dialog open={open} onClose={() => handleClose()} maxWidth="sm" fullWidth>
            <DialogTitle>
                Assign Users to Project
                <Typography component="div" variant="subtitle2" color="text.secondary">
                    {projectName}
                </Typography>
                {projectLanguage && (
                    <Typography component="div" variant="body2" color="primary" sx={{ mt: 0.5 }}>
                        Language: {projectLanguage}
                    </Typography>
                )}
            </DialogTitle>
            
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {isLoading ? (
                    <Box display="flex" justifyContent="center" p={2}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <FormControl fullWidth sx={{ mt: 2 }}>
                        <InputLabel id="users-select-label">Select Users</InputLabel>
                        <Select
                            labelId="users-select-label"
                            multiple
                            value={selectedUsers}
                            onChange={(e) => setSelectedUsers(e.target.value)}
                            renderValue={(selected) => (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {selected.map((value) => (
                                        <Chip key={value} label={value} size="small" />
                                    ))}
                                </Box>
                            )}
                            label="Select Users"
                        >
                            {availableUsers.length > 0 ? (
                                availableUsers.map((user) => (
                                    <MenuItem key={user} value={user}>
                                        {user}
                                    </MenuItem>
                                ))
                            ) : (
                                <MenuItem disabled>
                                    No users available for {projectLanguage || 'selected language'}
                                </MenuItem>
                            )}
                        </Select>
                    </FormControl>
                )}

                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Selected {selectedUsers.length} user(s)
                </Typography>
                
                {projectLanguage && availableUsers.length === 0 && !isLoading && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                        No users found for {projectLanguage}. Please make sure there are users registered for this language.
                    </Alert>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={() => handleClose()} disabled={isSubmitting}>
                    Cancel
                </Button>
                <Button 
                    onClick={handleAssignUsers}
                    variant="contained"
                    disabled={isSubmitting || selectedUsers.length === 0}
                >
                    {isSubmitting ? <CircularProgress size={24} /> : 'Assign Users'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}