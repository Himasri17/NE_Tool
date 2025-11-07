import React, { useState, useEffect } from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions,
    Button, Typography, Box, List, ListItem, ListItemText,
    Chip, Alert, Divider, CircularProgress, Grid, Paper
} from '@mui/material';
import AssignmentLateIcon from '@mui/icons-material/AssignmentLate';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { getToken, removeToken } from '../../components/authUtils'; 

const API_BASE_URL = 'http://127.0.0.1:5001';

export function SentencesRevisionNotesDialog({ 
    open, 
    onClose, 
    username,
    onNavigateToSentence 
}) {
    const [revisionNotes, setRevisionNotes] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch revision notes when dialog opens
    useEffect(() => {
        if (open && username) {
            fetchRevisionNotes();
        }
    }, [open, username]);

    const fetchRevisionNotes = async () => {
        try {
            setIsLoading(true);
            setError(null);
            
            const token = getToken();
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${API_BASE_URL}/api/annotator/revision_notes/${username}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired or invalid
                    removeToken();
                    window.location.href = '/'; // Redirect to login
                    return;
                }
                throw new Error(`Failed to fetch revision notes: ${response.status}`);
            }

            const notes = await response.json();
            setRevisionNotes(notes);
        } catch (error) {
            console.error('Error fetching revision notes:', error);
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAcknowledge = async (sentenceId) => {
        try {
            const token = getToken();
            const response = await fetch(`${API_BASE_URL}/api/annotator/acknowledge_revision`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sentence_id: sentenceId
                })
            });

            if (response.ok) {
                // Remove the acknowledged note from the list
                setRevisionNotes(prev => prev.filter(note => note.sentenceId !== sentenceId));
                
                // Call the parent callback to navigate to the sentence
                if (onNavigateToSentence) {
                    onNavigateToSentence(sentenceId);
                }
                
                // Close the dialog after navigation
                onClose();
            }
        } catch (err) {
            console.error('Error acknowledging revision:', err);
            setError('Failed to acknowledge revision. Please try again.');
        }
    };

    const formatTagDisplay = (tagObj) => {
        if (typeof tagObj === 'string') return tagObj;
        return `${tagObj.tag}: "${tagObj.text}"`;
    };

    return (
        <Dialog 
            open={open} 
            onClose={onClose}
            maxWidth="lg"
            fullWidth
        >
            <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <AssignmentLateIcon color="warning" />
                    <Typography variant="h6">Revision Notes - Feedback from Reviewer</Typography>
                    {revisionNotes.length > 0 && (
                        <Chip 
                            label={`${revisionNotes.length} pending`} 
                            color="warning" 
                            size="small" 
                        />
                    )}
                </Box>
            </DialogTitle>
            
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {isLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                        <CircularProgress />
                    </Box>
                ) : revisionNotes.length === 0 ? (
                    <Alert severity="info">
                        No pending revision notes. Great job! 🎉
                    </Alert>
                ) : (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {revisionNotes.map((note, index) => (
                            <Paper 
                                key={note.sentenceId || index}
                                elevation={1} 
                                sx={{ 
                                    p: 2,
                                    border: '1px solid',
                                    borderColor: note.rejectionType === 'tag' ? 'warning.light' : 'error.light',
                                    backgroundColor: note.rejectionType === 'tag' ? '#fffdf6' : '#fff5f5'
                                }}
                            >
                                <Grid container spacing={2} alignItems="stretch">
                                    {/* Sentence Column */}
                                    <Grid item xs={12} md={4}>
                                        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                                            <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                                                SENTENCE
                                            </Typography>
                                            <Paper 
                                                variant="outlined" 
                                                sx={{ 
                                                    p: 1.5, 
                                                    backgroundColor: 'white',
                                                    flex: 1,
                                                    display: 'flex',
                                                    flexDirection: 'column'
                                                }}
                                            >
                                                <Typography 
                                                    variant="body2" 
                                                    sx={{ 
                                                        fontStyle: 'italic', 
                                                        lineHeight: 1.4,
                                                        flex: 1
                                                    }}
                                                >
                                                    "{note.sentenceText}"
                                                </Typography>
                                            </Paper>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1, alignItems: 'center' }}>
                                                <Chip 
                                                    label={note.rejectionType === 'tag' ? 'Tag Rejection' : 'Sentence Rejection'}
                                                    color={note.rejectionType === 'tag' ? 'warning' : 'error'}
                                                    size="small"
                                                />
                                                <Typography variant="caption" color="text.secondary">
                                                    By {note.reviewer} • {note.rejectionDate}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Grid>

                                    {/* Rejected Tags Column */}
                                    {note.rejectedTags && note.rejectedTags.length > 0 && (
                                        <Grid item xs={12} md={3}>
                                            <Typography variant="subtitle2" fontWeight="bold" color="error" gutterBottom>
                                                REJECTED TAGS ({note.rejectedTags.length})
                                            </Typography>
                                            <Box sx={{ 
                                                display: 'flex', 
                                                flexWrap: 'wrap', 
                                                gap: 0.5
                                            }}>
                                                {note.rejectedTags.map((tagObj, tagIndex) => (
                                                    <Chip 
                                                        key={tagIndex}
                                                        label={formatTagDisplay(tagObj)}
                                                        color="error"
                                                        size="small"
                                                        variant="outlined"
                                                    />
                                                ))}
                                            </Box>
                                        </Grid>
                                    )}

                                    {/* Feedback Column */}
                                    <Grid item xs={12} md={note.rejectedTags?.length > 0 ? 3 : 4}>
                                        <Typography variant="subtitle2" fontWeight="bold" color="text.secondary" gutterBottom>
                                            REVIEWER FEEDBACK
                                        </Typography>
                                        <Typography 
                                            variant="body2" 
                                            sx={{ 
                                                lineHeight: 1.4,
                                                color: 'text.primary'
                                            }}
                                        >
                                            {note.reviewerComment || "No specific feedback provided."}
                                        </Typography>
                                    </Grid>

                                    {/* Action Column */}
                                    <Grid item xs={12} md={2}>
                                        <Box sx={{ 
                                            height: '100%', 
                                            display: 'flex', 
                                            flexDirection: 'column',
                                            justifyContent: 'center'
                                        }}>
                                            <Button
                                                variant="contained"
                                                color="warning"
                                                onClick={() => handleAcknowledge(note.sentenceId)}
                                                size="medium"
                                                startIcon={<VisibilityIcon />}
                                                fullWidth
                                                sx={{ 
                                                    whiteSpace: 'nowrap',
                                                    py: 1
                                                }}
                                            >
                                                Revise Now
                                            </Button>
                                        </Box>
                                    </Grid>
                                </Grid>
                            </Paper>
                        ))}
                    </Box>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} color="primary">
                    Close
                </Button>
                {revisionNotes.length > 0 && (
                    <Button 
                        onClick={fetchRevisionNotes} 
                        color="secondary"
                        disabled={isLoading}
                    >
                        Refresh
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
}