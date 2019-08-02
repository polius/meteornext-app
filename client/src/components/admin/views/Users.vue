<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">USERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newItem()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editItem()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteItem()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:items="props">
          <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
          <td>{{ props.item.username }}</td>
          <td>{{ props.item.group }}</td>
          <td>{{ props.item.mail }}</td>
          <td>{{ props.item.password }}</td>
          <td v-if="props.item.admin"><v-icon small color="success" style="margin-left:8px;">fas fa-check</v-icon></td>
          <td v-else><v-icon small color="error" style="margin-left:8px;">fas fa-times</v-icon></td>
        </template>
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning" style="margin-top:15px;">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="itemDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ itemDialogTitle }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="itemDialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <v-text-field ref="field" v-model="item.username" label="Username" required append-icon="person" style="padding-top:0px;"></v-text-field>
                <v-text-field v-model="item.email" label="Email" type="email" required append-icon="email" style="padding-top:0px; margin-top:0px;"></v-text-field>
                <v-text-field v-model="item.password" label="Password" type="password" required append-icon="lock" style="padding-top:0px; margin-top:0px;"></v-text-field>
                <v-select v-model="item.group" :items="groups_items" label="Group" required style="padding-top:0px; margin-top:0px;"></v-select>
                <v-switch v-model="item.admin" hint="yes" label="Admin Privileges" style="margin-top:0px; padding-top:0px;"></v-switch>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected users?</div>
              </v-flex>
              <v-btn color="success" @click="actionConfirm()">Confirm</v-btn>
              <v-btn color="error" @click="itemDialog=false" style="margin-left:10px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    // Data Table
    headers: [
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Email', align: 'left', value: 'email'},
      { text: 'Password', align: 'left', value: 'password'},
      { text: 'Admin', align: 'left', value: 'admin'},
    ],
    items: [
      {
        id: 1,
        username: 'palzina',
        group: 'Administrator',
        email: 'palzina@inbenta.com',
        password: '12345',
        admin: true
      }
    ],
    selected: [],
    search: '',
    // Item
    item: { username: '', group: '', email: '', password: '', admin: ''},
    groups_items: [],
    // Action Mode (new, edit, delete)
    mode: '',
    // Dialog: Item
    itemDialog: false,
    itemDialogTitle: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  methods: {
    getItems() {
      const path = 'http://34.242.255.177:5000/admin/users/'
      axios.get(path)
        .then((res) => {
          this.items = res.data.items
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newItem() {
      this.mode = 'new'
      this.item= { username: '', group: '', email: '', password: '', admin: '' }
      this.itemDialogTitle = 'New User'
      this.itemDialog = true
    },
    editItem() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.itemDialogTitle = 'Edit User'
      this.itemDialog = true
    },
    deleteItem() {
      this.mode = 'delete'
      this.itemDialogTitle = 'Delete User'
      this.itemDialog = true
    },
    actionConfirm() {
      if (this.mode == 'new') this.newItemConfirm()
      else if (this.mode == 'edit') this.editItemConfirm()
      else if (this.mode == 'delete') this.deleteItemConfirm()
    },
    newItemConfirm() {
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.item.username) {
          this.notification('User currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.items.push(this.item)
      this.itemDialog = false
      this.notification('User added successfully', 'success')
    },
    editItemConfirm() {
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.selected[0]['username']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['username'] == this.item.username && this.item.username != this.selected[0]['username']) {
          this.notification('User currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.items.splice(i, 1, this.item)
      this.itemDialog = false
      this.notification('User edited successfully', 'success')
    },
    deleteItemConfirm() {
      while(this.selected.length > 0) {
        var s = this.selected.pop()
        for (var i = 0; i < this.items.length; ++i) {
          if (this.items[i]['id'] == s['id']) {
            // Delete Item
            this.items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected users removed successfully', 'success')
      this.itemDialog = false
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    itemDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script> 