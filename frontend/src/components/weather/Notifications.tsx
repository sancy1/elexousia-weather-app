// import { useState, useEffect } from "react";
// import { Bell, X, Check, Trash2 } from "lucide-react";
// import { weatherApi } from "@/lib/weather";
// import type { Notification } from "@/lib/api-types";

// interface Props {
//   user: any;
// }

// export function Notifications({ user }: Props) {
//   const [isOpen, setIsOpen] = useState(false);
//   const [notifications, setNotifications] = useState<Notification[]>([]);
//   const [unreadCount, setUnreadCount] = useState(0);
//   const [loading, setLoading] = useState(false);

//   useEffect(() => {
//     if (user) {
//       fetchNotifications();
//     }
//   }, [user]);

//   const fetchNotifications = async () => {
//     if (!user) return;
//     setLoading(true);
//     try {
//       const response = await weatherApi.getNotifications();
//       setNotifications(response.notifications);
//       setUnreadCount(response.unread_count);
//     } catch (error) {
//       console.error("Failed to fetch notifications:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const markAsRead = async (notificationId: number) => {
//     try {
//       await weatherApi.markNotificationAsRead(notificationId);
//       setNotifications((prev) =>
//         prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
//       );
//       setUnreadCount((prev) => Math.max(0, prev - 1));
//     } catch (error) {
//       console.error("Failed to mark notification as read:", error);
//     }
//   };

//   const markAllAsRead = async () => {
//     try {
//       await weatherApi.markAllNotificationsAsRead();
//       setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
//       setUnreadCount(0);
//     } catch (error) {
//       console.error("Failed to mark all as read:", error);
//     }
//   };

//   const deleteNotification = async (notificationId: number) => {
//     try {
//       await weatherApi.deleteNotification(notificationId);
//       setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
//       const deleted = notifications.find((n) => n.id === notificationId);
//       if (deleted && !deleted.is_read) {
//         setUnreadCount((prev) => Math.max(0, prev - 1));
//       }
//     } catch (error) {
//       console.error("Failed to delete notification:", error);
//     }
//   };

//   // const deleteAllNotifications = async () => {
//   //   try {
//   //     await weatherApi.deleteAllNotifications();
//   //     setNotifications([]);
//   //     setUnreadCount(0);
//   //   } catch (error) {
//   //     console.error("Failed to delete all notifications:", error);
//   //   }
//   // };

//   const deleteAllNotifications = async () => {
//   if (notifications.length === 0) return;
  
//   // Confirm before deleting
//   const confirmed = window.confirm(
//       "⚠️ Delete all notifications?\n\nThis action cannot be undone. All notifications will be permanently deleted."
//     );
    
//     if (!confirmed) return;
    
//     try {
//       await weatherApi.deleteAllNotifications();
//       setNotifications([]);
//       setUnreadCount(0);
//     } catch (error) {
//       console.error("Failed to delete all notifications:", error);
//       alert("Failed to delete notifications. Please try again.");
//     }
//   };

//   const getNotificationIcon = (type: Notification["type"]) => {
//     switch (type) {
//       case "rain_alert":
//         return "🌧️";
//       case "heat_alert":
//         return "🔥";
//       case "cold_alert":
//         return "❄️";
//       default:
//         return "ℹ️";
//     }
//   };

//   const getNotificationColor = (type: Notification["type"]) => {
//     switch (type) {
//       case "rain_alert":
//         return "text-blue-400";
//       case "heat_alert":
//         return "text-orange-400";
//       case "cold_alert":
//         return "text-cyan-400";
//       default:
//         return "text-muted-foreground";
//     }
//   };

//   if (!user) return null;

//   return (
//     <div className="relative">
//       <button
//         onClick={() => {
//           setIsOpen(!isOpen);
//           if (!isOpen) fetchNotifications();
//         }}
//         className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors relative"
//       >
//         <Bell className="h-4 w-4" />
//         {unreadCount > 0 && (
//           <span className="absolute -top-0.5 -right-0.5 h-5 w-5 rounded-full bg-destructive text-[10px] font-semibold text-white flex items-center justify-center shadow-[0_0_10px_-2px_var(--destructive)]">
//             {unreadCount > 9 ? "9+" : unreadCount}
//           </span>
//         )}
//       </button>

//       {isOpen && (
//         <>
//           <div
//             className="fixed inset-0 z-40"
//             onClick={() => setIsOpen(false)}
//           />
//           <div className="absolute right-0 top-12 z-50 w-[380px] max-h-[500px] bg-card border border-border rounded-2xl shadow-[0_8px_40px_-12px_rgba(0,0,0,0.3)] overflow-hidden">
//             <div className="p-4 border-b border-border flex items-center justify-between">
//               <h3 className="text-sm font-semibold">Notifications</h3>
//               <div className="flex items-center gap-2">
                
//                 {unreadCount > 0 && (
//                   <button
//                     onClick={markAllAsRead}
//                     className="text-xs text-primary hover:text-primary/80 transition-colors"
//                   >
//                     Mark all read
//                   </button>
//                 )}

//                 {notifications.length > 0 && (
//                   <button
//                     onClick={deleteAllNotifications}
//                     className="text-xs text-destructive hover:text-destructive/80 transition-colors"
//                   >
//                     Delete all
//                   </button>
//                 )}

//                 <button
//                   onClick={() => setIsOpen(false)}
//                   className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
//                 >
//                   <X className="h-3.5 w-3.5" />
//                 </button>
//               </div>
//             </div>

//             <div className="overflow-y-auto max-h-[420px]">
//               {loading ? (
//                 <div className="p-8 text-center text-sm text-muted-foreground">
//                   Loading notifications...
//                 </div>
//               ) : notifications.length === 0 ? (
//                 <div className="p-8 text-center">
//                   <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mx-auto mb-3">
//                     <Bell className="h-5 w-5 text-muted-foreground" />
//                   </div>
//                   <p className="text-sm text-muted-foreground">No notifications yet</p>
//                 </div>
//               ) : (
//                 <div className="divide-y divide-border">
//                   {notifications.map((notification) => (
//                     <div
//                       key={notification.id}
//                       className={`p-4 hover:bg-accent/30 transition-colors ${
//                         !notification.is_read ? "bg-primary/5" : ""
//                       }`}
//                     >
//                       <div className="flex gap-3">
//                         <div className="h-9 w-9 rounded-lg bg-secondary flex items-center justify-center shrink-0">
//                           <span className="text-lg">
//                             {getNotificationIcon(notification.type)}
//                           </span>
//                         </div>
//                         <div className="flex-1 min-w-0">
//                           <div className="flex items-start justify-between gap-2 mb-1">
//                             <h4 className="text-sm font-medium truncate">
//                               {notification.title}
//                             </h4>
//                             {!notification.is_read && (
//                               <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5" />
//                             )}
//                           </div>
//                           <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
//                             {notification.message}
//                           </p>
//                           <p className="text-[10px] text-muted-foreground">
//                             {new Date(notification.created_at).toLocaleString()}
//                           </p>
//                         </div>
//                         <div className="flex flex-col gap-1 shrink-0">
//                           {!notification.is_read && (
//                             <button
//                               onClick={() => markAsRead(notification.id)}
//                               className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
//                               title="Mark as read"
//                             >
//                               <Check className="h-3 w-3" />
//                             </button>
//                           )}
//                           <button
//                             onClick={() => deleteNotification(notification.id)}
//                             className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-destructive transition-colors"
//                             title="Delete"
//                           >
//                             <Trash2 className="h-3 w-3" />
//                           </button>
//                         </div>
//                       </div>
//                     </div>
//                   ))}
//                 </div>
//               )}
//             </div>
//           </div>
//         </>
//       )}
//     </div>
//   );
// }





























// import { useState, useEffect } from "react";
// import { Bell, X, Check, Trash2 } from "lucide-react";
// import { weatherApi } from "@/lib/weather";
// import type { Notification } from "@/lib/api-types";

// interface Props {
//   user: any;
// }

// export function Notifications({ user }: Props) {
//   const [isOpen, setIsOpen] = useState(false);
//   const [notifications, setNotifications] = useState<Notification[]>([]);
//   const [unreadCount, setUnreadCount] = useState(0);
//   const [loading, setLoading] = useState(false);

//   useEffect(() => {
//     if (user) {
//       fetchNotifications();
//     }
//   }, [user]);

//   const fetchNotifications = async () => {
//     if (!user) return;
//     setLoading(true);
//     try {
//       const response = await weatherApi.getNotifications();
//       setNotifications(response.notifications);
//       setUnreadCount(response.unread_count);
//     } catch (error) {
//       console.error("Failed to fetch notifications:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const markAsRead = async (notificationId: number) => {
//     try {
//       await weatherApi.markNotificationAsRead(notificationId);
//       setNotifications((prev) =>
//         prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
//       );
//       setUnreadCount((prev) => Math.max(0, prev - 1));
//     } catch (error) {
//       console.error("Failed to mark notification as read:", error);
//     }
//   };

//   const markAllAsRead = async () => {
//     try {
//       await weatherApi.markAllNotificationsAsRead();
//       setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
//       setUnreadCount(0);
//     } catch (error) {
//       console.error("Failed to mark all as read:", error);
//     }
//   };

//   const deleteNotification = async (notificationId: number) => {
//     try {
//       await weatherApi.deleteNotification(notificationId);
//       setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
//       const deleted = notifications.find((n) => n.id === notificationId);
//       if (deleted && !deleted.is_read) {
//         setUnreadCount((prev) => Math.max(0, prev - 1));
//       }
//     } catch (error) {
//       console.error("Failed to delete notification:", error);
//     }
//   };

//   const deleteAllNotifications = async () => {
//     if (notifications.length === 0) return;
//     const confirmed = window.confirm(
//       "⚠️ Delete all notifications?\n\nThis action cannot be undone."
//     );
//     if (!confirmed) return;
//     try {
//       await weatherApi.deleteAllNotifications();
//       setNotifications([]);
//       setUnreadCount(0);
//     } catch (error) {
//       console.error("Failed to delete all notifications:", error);
//     }
//   };

//   const getNotificationIcon = (type: Notification["type"]) => {
//     switch (type) {
//       case "rain_alert": return "🌧️";
//       case "heat_alert": return "🔥";
//       case "cold_alert": return "❄️";
//       default: return "ℹ️";
//     }
//   };

//   if (!user) return null;

//   return (
//     <div className="relative">
//       <button
//         onClick={() => {
//           setIsOpen(!isOpen);
//           if (!isOpen) fetchNotifications();
//         }}
//         className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors relative"
//       >
//         <Bell className="h-4 w-4" />
//         {unreadCount > 0 && (
//           <span className="absolute -top-0.5 -right-0.5 h-5 w-5 rounded-full bg-destructive text-[10px] font-semibold text-white flex items-center justify-center shadow-[0_0_10px_-2px_var(--destructive)]">
//             {unreadCount > 9 ? "9+" : unreadCount}
//           </span>
//         )}
//       </button>

//       {isOpen && (
//         <>
//           {/* Overlay */}
//           <div
//             className="fixed inset-0 z-40 bg-background/20 backdrop-blur-sm sm:bg-transparent"
//             onClick={() => setIsOpen(false)}
//           />

//           {/* 
//               RESPONSIVE MODAL LOGIC:
//               - Mobile: fixed position, centered, max-width 95vw to prevent touching edges.
//               - Desktop (sm): absolute position, anchored to the right of the button.
//           */}
//           <div className="fixed sm:absolute left-1/2 sm:left-auto right-auto sm:right-0 top-20 sm:top-12 -translate-x-1/2 sm:translate-x-0 z-50 w-[95vw] sm:w-[380px] max-h-[80vh] sm:max-h-[500px] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            
//             {/* Header: Flex wrap ensures buttons don't disappear on very small screens */}
//             <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-2 sticky top-0 bg-card z-10">
//               <h3 className="text-sm font-semibold shrink-0">Notifications</h3>
//               <div className="flex items-center gap-3">
//                 {unreadCount > 0 && (
//                   <button
//                     onClick={markAllAsRead}
//                     className="text-xs text-primary font-medium hover:underline transition-all"
//                   >
//                     Mark all read
//                   </button>
//                 )}

//                 {notifications.length > 0 && (
//                   <button
//                     onClick={deleteAllNotifications}
//                     className="text-xs text-destructive font-medium hover:underline transition-all"
//                   >
//                     Delete all
//                   </button>
//                 )}

//                 <button
//                   onClick={() => setIsOpen(false)}
//                   className="h-8 w-8 flex items-center justify-center rounded-full bg-accent/50 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
//                 >
//                   <X className="h-4 w-4" />
//                 </button>
//               </div>
//             </div>

//             {/* Scrollable Content */}
//             <div className="overflow-y-auto flex-1">
//               {loading ? (
//                 <div className="p-8 text-center text-sm text-muted-foreground">
//                   Loading notifications...
//                 </div>
//               ) : notifications.length === 0 ? (
//                 <div className="p-12 text-center">
//                   <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mx-auto mb-3">
//                     <Bell className="h-5 w-5 text-muted-foreground" />
//                   </div>
//                   <p className="text-sm text-muted-foreground">No notifications yet</p>
//                 </div>
//               ) : (
//                 <div className="divide-y divide-border">
//                   {notifications.map((notification) => (
//                     <div
//                       key={notification.id}
//                       className={`p-4 hover:bg-accent/30 transition-colors ${
//                         !notification.is_read ? "bg-primary/5 border-l-2 border-l-primary" : ""
//                       }`}
//                     >
//                       <div className="flex gap-3">
//                         <div className="h-9 w-9 rounded-lg bg-secondary flex items-center justify-center shrink-0">
//                           <span className="text-lg">
//                             {getNotificationIcon(notification.type)}
//                           </span>
//                         </div>
//                         <div className="flex-1 min-w-0">
//                           <div className="flex items-start justify-between gap-2 mb-1">
//                             <h4 className="text-sm font-semibold truncate leading-none pt-1">
//                               {notification.title}
//                             </h4>
//                           </div>
//                           <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
//                             {notification.message}
//                           </p>
//                           <p className="text-[10px] text-muted-foreground/70 uppercase font-medium">
//                             {new Date(notification.created_at).toLocaleDateString()} • {new Date(notification.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
//                           </p>
//                         </div>
//                         <div className="flex flex-col gap-2 shrink-0">
//                           {!notification.is_read && (
//                             <button
//                               onClick={() => markAsRead(notification.id)}
//                               className="h-7 w-7 flex items-center justify-center rounded-md bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors"
//                               title="Mark as read"
//                             >
//                               <Check className="h-4 w-4" />
//                             </button>
//                           )}
//                           <button
//                             onClick={() => deleteNotification(notification.id)}
//                             className="h-7 w-7 flex items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-colors"
//                             title="Delete"
//                           >
//                             <Trash2 className="h-4 w-4" />
//                           </button>
//                         </div>
//                       </div>
//                     </div>
//                   ))}
//                 </div>
//               )}
//             </div>
//           </div>
//         </>
//       )}
//     </div>
//   );
// }































import { useState, useEffect } from "react";
import { Bell, X, Check, Trash2 } from "lucide-react";
import { weatherApi } from "@/lib/weather";
import type { Notification } from "@/lib/api-types";

interface Props {
  user: any;
}

export function Notifications({ user }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetchNotifications();
    }
  }, [user]);

  const fetchNotifications = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await weatherApi.getNotifications();
      setNotifications(response.notifications);
      setUnreadCount(response.unread_count);
    } catch (error) {
      console.error("Failed to fetch notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      await weatherApi.markNotificationAsRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await weatherApi.markAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error("Failed to mark all as read:", error);
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      await weatherApi.deleteNotification(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      const deleted = notifications.find((n) => n.id === notificationId);
      if (deleted && !deleted.is_read) {
        setUnreadCount((prev) => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error("Failed to delete notification:", error);
    }
  };

  const deleteAllNotifications = async () => {
    if (notifications.length === 0) return;
    const confirmed = window.confirm(
      "⚠️ Delete all notifications?\n\nThis action cannot be undone."
    );
    if (!confirmed) return;
    try {
      await weatherApi.deleteAllNotifications();
      setNotifications([]);
      setUnreadCount(0);
    } catch (error) {
      console.error("Failed to delete all notifications:", error);
    }
  };

  const getNotificationIcon = (type: Notification["type"]) => {
    switch (type) {
      case "rain_alert": return "🌧️";
      case "heat_alert": return "🔥";
      case "cold_alert": return "❄️";
      default: return "ℹ️";
    }
  };

  if (!user) return null;

  return (
    <div className="relative z-[50]">
      {/* Trigger Button */}
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) fetchNotifications();
        }}
        className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors relative z-[52]"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-5 w-5 rounded-full bg-destructive text-[10px] font-semibold text-white flex items-center justify-center shadow-sm">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          {/* 
            Invisible Click-Catcher: 
            Removed bg-background/20 and backdrop-blur-sm to keep background sharp.
          */}
          <div
            className="fixed inset-0 z-40 bg-transparent"
            onClick={() => setIsOpen(false)}
          />

          {/* 
            Tray Container:
            Responsive centered mobile logic + Desktop drop-right alignment.
          */}
          <div className="fixed sm:absolute left-1/2 sm:left-auto right-auto sm:right-0 top-20 sm:top-12 -translate-x-1/2 sm:translate-x-0 z-50 w-[95vw] sm:w-[380px] max-h-[80vh] sm:max-h-[500px] bg-card border border-border rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden flex flex-col">
            
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-2 sticky top-0 bg-card z-10">
              <h3 className="text-sm font-semibold shrink-0">Notifications</h3>
              <div className="flex items-center gap-3">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-primary font-medium hover:underline transition-all"
                  >
                    Mark all read
                  </button>
                )}

                {notifications.length > 0 && (
                  <button
                    onClick={deleteAllNotifications}
                    className="text-xs text-destructive font-medium hover:underline transition-all"
                  >
                    Delete all
                  </button>
                )}

                <button
                  onClick={() => setIsOpen(false)}
                  className="h-8 w-8 flex items-center justify-center rounded-full bg-accent/50 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            {/* <div className="overflow-y-auto flex-1"> */}
            <div className="overflow-y-auto flex-1 scrollbar-thin scrollbar-track-background/20 scrollbar-thumb-primary/50 hover:scrollbar-thumb-primary/70">
              {loading ? (
                <div className="p-8 text-center text-sm text-muted-foreground">
                  Loading notifications...
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="h-12 w-12 rounded-full bg-secondary flex items-center justify-center mx-auto mb-3">
                    <Bell className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">No notifications yet</p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-accent/30 transition-colors ${
                        !notification.is_read ? "bg-primary/5 border-l-2 border-l-primary" : ""
                      }`}
                    >
                      <div className="flex gap-3">
                        <div className="h-9 w-9 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                          <span className="text-lg">
                            {getNotificationIcon(notification.type)}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h4 className="text-sm font-semibold truncate leading-none pt-1">
                              {notification.title}
                            </h4>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                            {notification.message}
                          </p>
                          <div className="flex items-center gap-2">
                            <p className="text-[10px] text-muted-foreground/70 uppercase font-medium">
                              {new Date(notification.created_at).toLocaleDateString()}
                            </p>
                            <span className="text-[10px] text-muted-foreground/40">•</span>
                            <p className="text-[10px] text-muted-foreground/70 uppercase font-medium">
                              {new Date(notification.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col gap-2 shrink-0">
                          {!notification.is_read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="h-7 w-7 flex items-center justify-center rounded-md bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors"
                              title="Mark as read"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="h-7 w-7 flex items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}