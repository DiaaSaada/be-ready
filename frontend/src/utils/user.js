/**
 * User ID utility for progress tracking.
 * Since we don't have authentication yet, we use a localStorage UUID.
 */

const USER_ID_KEY = 'beready_user_id';

/**
 * Get the current user ID.
 * Creates a new UUID if one doesn't exist.
 * @returns {string} User ID
 */
export const getUserId = () => {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
};

/**
 * Clear the user ID (useful for testing or logout).
 */
export const clearUserId = () => {
  localStorage.removeItem(USER_ID_KEY);
};

/**
 * Check if user has an existing ID.
 * @returns {boolean}
 */
export const hasUserId = () => {
  return localStorage.getItem(USER_ID_KEY) !== null;
};
