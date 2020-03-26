import Vue from 'vue'
import VueRouter from 'vue-router'
import store from './../store'

Vue.use(VueRouter)

let router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../components/Home'),
      meta: { requiresAuth: true }  
    },
    {
      path: '/setup',
      name: 'setup',
      props: true,
      component: () => import('../components/Setup'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      props: true,
      component: () => import('../components/Login'),
      meta: { requiresAuth: false }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../components/Profile'),
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../components/Notifications'),
      meta: { requiresAuth: true }
    },
    {
      path: '/inventory',
      component: () => import('../components/inventory/Navigation'),
      meta: { requiresAuth: true, requiresInventory: true },
      children: [
        {
          path: '',
          name: 'inventory',
          component: () => import('../components/inventory/Inventory'),
          meta: { requiresAuth: true, requiresInventory: true }
        },
        {
          path: 'environments',
          name: 'inventory.environments',
          component: () => import('../components/inventory/views/Environments'),
          meta: { requiresAuth: true, requiresInventory: true }
        },
        {
          path: 'regions',
          name: 'inventory.regions',
          component: () => import('../components/inventory/views/Regions'),
          meta: { requiresAuth: true, requiresInventory: true }
        },
        {
          path: 'servers',
          name: 'inventory.servers',
          component: () => import('../components/inventory/views/Servers'),
          meta: { requiresAuth: true, requiresInventory: true }
        },
        {
          path: 'auxiliary',
          name: 'inventory.auxiliary',
          component: () => import('../components/inventory/views/Auxiliary'),
          meta: { requiresAuth: true, requiresInventory: true }
        },
        {
          path: 'slack',
          name: 'inventory.slack',
          component: () => import('../components/inventory/views/Slack'),
          meta: { requiresAuth: true, requiresInventory: true }
        }
      ]
    },
    {
      path: '/deployments',
      component: () => import('../components/deployments/Navigation'),
      meta: { requiresAuth: true, requiresDeployments: true },
      children: [
        {
          path: '',
          name: 'deployments',
          component: () => import('../components/deployments/Deployments'),
          meta: { requiresAuth: true, requiresDeployments: true }
        },
        {
          path: 'releases',
          name: 'deployments.releases',
          component: () => import('../components/deployments/Releases'),
          meta: { requiresAuth: true, requiresDeployments: true }
        },
        {
          path: 'new',
          name: 'deployments.new',
          component: () => import('../components/deployments/views/Navigation'),
          meta: { requiresAuth: true, requiresDeployments: true }
        }
      ]
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('../components/deployments/Results'),
      meta: { requiresAuth: true }
    },
    {
      path: '/results/:uri',
      name: 'results_uri',
      component: () => import('../components/deployments/Results'),
      meta: { requiresAuth: true }
    },
    {
      path: '/deployment',
      component: () => import('../components/deployments/Navigation'),
      meta: { requiresAuth: true },
      children: [
        {
          path: ':id',
          name: 'deployment',
          component: () => import('../components/deployments/Deployment'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/monitoring',
      meta: { requiresAuth: true },
      component: () => import('../components/monitoring/Navigation'),
      children: [
        {
          path: '',
          name: 'monitoring',
          component: () => import('../components/monitoring/Monitoring'),
          meta: { requiresAuth: true }
        },
        {
          path: 'processlist',
          name: 'monitoring.processlist',
          component: () => import('../components/monitoring/views/Processlist'),
          meta: { requiresAuth: true }
        },
        {
          path: 'queries',
          name: 'monitoring.queries',
          component: () => import('../components/monitoring/views/Queries'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/utils',
      meta: { requiresAuth: true },
      component: () => import('../components/utils/Navigation'),
      children: [
        {
          path: '',
          name: 'utils',
          component: () => import('../components/utils/Utils'),
          meta: { requiresAuth: true }
        },
        {
          path: 'compare',
          name: 'utils.compare',
          component: () => import('../components/utils/views/Compare'),
          meta: { requiresAuth: true }
        },
        {
          path: 'manage',
          name: 'utils.manage',
          component: () => import('../components/utils/views/Manage'),
          meta: { requiresAuth: true }
        },
        {
          path: 'restore',
          name: 'utils.restore',
          component: () => import('../components/utils/views/Restore'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/client',
      meta: { requiresAuth: true },
      component: () => import('../components/client/Navigation')
    },
    {
      path: '/admin',
      component: () => import('../components/admin/Navigation'),
      meta: {requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin',
          component: () => import('../components/admin/Admin'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'settings',
          name: 'admin.settings',
          component: () => import('../components/admin/views/Settings'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'users',
          name: 'admin.users',
          component: () => import('../components/admin/views/Users'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'groups',
          name: 'admin.groups',
          component: () => import('../components/admin/views/Groups'),
          meta: { requiresAdmin: true },
          children: [
            {
              path: ':id',
              name: 'admin.group',
              component: () => import('../components/admin/views/Group'),
              meta: { requiresAuth: true }
            }
          ]
        },
        {
          path: 'inventory',
          name: 'admin.inventory',
          component: () => import('../components/admin/views/Inventory'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'deployments',
          name: 'admin.deployments',
          component: () => import('../components/admin/views/Deployments'),
          meta: { requiresAdmin: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.path == '/login' && store.getters.isLoggedIn) next('/')
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (store.getters.isLoggedIn) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresAdmin)) {
    if (store.getters.isLoggedIn && store.getters.admin) next()
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresInventory)) {
    if (store.getters.isLoggedIn && store.getters.inventory_enable) next()
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresDeployments)) {
    if (store.getters.isLoggedIn && store.getters.deployments_enable) next()
    else next({ path: '/login' })
  }
  else next()
})

export default router