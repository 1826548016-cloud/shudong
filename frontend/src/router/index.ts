import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomePage.vue') },
    { path: '/about', name: 'about', component: () => import('../views/AboutMe.vue') },
    { path: '/music', name: 'music', component: () => import('../views/MusicLibrary.vue') },
    { path: '/messages', name: 'messages', component: () => import('../views/MessageBoard.vue') },
    { path: '/posts/:id', name: 'post-detail', component: () => import('../views/PostDetail.vue') },
    { path: '/admin/login', name: 'admin-login', component: () => import('../views/AdminLogin.vue') },
    { path: '/admin/editor', name: 'admin-editor', component: () => import('../views/AdminEditor.vue') },
    { path: '/admin/announcements', name: 'admin-announcements', component: () => import('../views/AdminAnnouncements.vue') },
    { path: '/admin/reviews', name: 'admin-reviews', component: () => import('../views/AdminReviews.vue') },
    { path: '/admin/inbox', name: 'admin-inbox', component: () => import('../views/AdminInbox.vue') },
    { path: '/profile', name: 'profile', component: () => import('../views/ProfileEditor.vue') },
    { path: '/ai-chat', name: 'ai-chat', component: () => import('../views/AIChat.vue'), meta: { hideTopbar: true } },
    { path: '/connection', name: 'connection', component: () => import('../views/connection.vue'), meta: { hideTopbar: true } },
    { path: '/timeline', name: 'timeline', component: () => import('../views/TimelineGallery.vue'), meta: { hideTopbar: true } },
  ],
})

export default router
