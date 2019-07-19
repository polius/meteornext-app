import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../components/Home')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../components/Login')
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../components/Profile')
  },
  {
    path: '/deployments',
    name: 'deployments',
    component: () => import('../components/deployments/Navigation'),
    children: [
      {
        path: '',
        name: 'deployments.',
        component: () => import('../components/deployments/Deployments')
      },
      {
        path: 'info',
        name: 'deployments.info',
        props: true,
        component: () => import('../components/deployments/Info')
      },
      {
        path: 'new',
        name: 'deployments.new',
        component: () => import('../components/deployments/new/Navigation')
      },
      {
        path: 'environments',
        name: 'deployments.environments',
        component: () => import('../components/deployments/settings/Environments')
      },
      {
        path: 'regions',
        name: 'deployments.regions',
        component: () => import('../components/deployments/settings/Regions')
      },
      {
        path: 'servers',
        name: 'deployments.servers',
        component: () => import('../components/deployments/settings/Servers')
      },
      {
        path: 'auxiliary',
        name: 'deployments.auxiliary',
        component: () => import('../components/deployments/settings/Auxiliary')
      },
      {
        path: 'slack',
        name: 'deployments.slack',
        component: () => import('../components/deployments/settings/Slack')
      },
      {
        path: 's3',
        name: 'deployments.s3',
        component: () => import('../components/deployments/settings/S3')
      },
      {
        path: 'web',
        name: 'deployments.web',
        component: () => import('../components/deployments/settings/Web')
      }
    ]
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: () => import('../components/monitoring/Navigation'),
    children: [
      {
        path: '',
        name: 'monitoring.',
        component: () => import('../components/monitoring/Monitoring')
      },
      {
        path: 'queries',
        name: 'monitoring.queries',
        component: () => import('../components/monitoring/views/Queries')
      }
    ]
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../components/admin/Navigation'),
    children: [
      {
        path: '',
        name: 'admin.',
        component: () => import('../components/admin/Admin')
      },
      {
        path: 'users',
        name: 'admin.users',
        component: () => import('../components/admin/views/Users')
      },
      {
        path: 'groups',
        name: 'admin.groups',
        component: () => import('../components/admin/views/Groups')
      }
    ]
  }
]

export default new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})