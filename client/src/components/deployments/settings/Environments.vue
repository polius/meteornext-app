<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">ENVIRONMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newItem()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editItem()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteItem()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:items="props">
          <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
          <td>{{ props.item.name }}</td>
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
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <v-text-field ref="field" v-on:keyup.enter="actionConfirm()" v-model="item.name" label="Environment Name" required></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected environments?</div>
              </v-flex>
              <v-btn color="success" @click="actionConfirm()">Confirm</v-btn>
              <v-btn color="error" @click="itemDialog=false" style="margin-left:10px;">Cancel</v-btn>
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
import axios from 'axios'

export default {
  data: () => ({
    // Data Table
    headers: [{ text: 'Name', align: 'left', value: 'name' }],
    items: [{ name: 'PRODUCTION' }],
    selected: [],
    search: '',
    // Item
    item: { name: '' },
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
      const path = 'http://34.242.255.177:5000/environments'
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
      this.item = { name: '' }
      this.itemDialogTitle = 'New Environment'
      this.itemDialog = true
    },
    editItem() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.itemDialogTitle = 'Edit Environment'
      this.itemDialog = true
    },
    deleteItem() {
      this.mode = 'delete'
      this.itemDialogTitle = 'Delete Environment'
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
        if (this.items[i]['name'] == this.item.name) {
          this.notification('Environment currently exists', 'error')
          return
        }
      }
      // Add item in the DB
      const path = 'http://34.242.255.177:5000/environments'
      const payload = this.item
      axios.post(path, payload)
        .then(() => {
          // Add item in the data table
          this.items.push(this.item)
          this.itemDialog = false
          this.notification('Environment added successfully', 'success')
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error)
          this.notification('Cannot add the environment. ' + error, 'error')
        })
    },
    editItemConfirm() {
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('Environment currently exists', 'error')
          return
        }
      }
      // Edit item in the DB
      //const path = `http://34.242.255.177:5000/books/${itemID}`;
      const path = ''
      const payload = this.item
      axios.put(path, payload)
        .then(() => {
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
          this.itemDialog = false
          this.notification('Environment edited successfully', 'success')
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error)
          this.notification('Cannot edit the environment. ' + error, 'error')
        })
    },
    deleteItemConfirm() {
      while(this.selected.length > 0) {
        var s = this.selected.pop()
        for (var i = 0; i < this.items.length; ++i) {
          if (this.items[i]['name'] == s['name']) {
            // Delete Item
            this.items.splice(i, 1)
            break
          }
        }
      }
      // Delete item in the DB
      // const path = `http://34.242.255.177:5000/books/${environmentID}`;
      // axios.delete(path)
      //   .then(() => {
      //     this.notification('Environments deleted successfully', 'success')
      //     this.confirmationDialog = false
      //   })
      //   .catch((error) => {
      //     // eslint-disable-next-line
      //     console.error(error);
      //   });
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  created() {
    this.getItems()
  },
  watch: {
    itemDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        this.$refs.field.focus()
      })
    }
  }
}
</script>