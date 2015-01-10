// -*- C++ -*-
#include <Python.h>
#include <string>
#include <sstream>
#include "structmember.h"
#include "internal.pb.h"

#include <google/protobuf/io/coded_stream.h>
#include <google/protobuf/io/zero_copy_stream_impl_lite.h>




static PyObject *
fastpb_convert5(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert3(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert18(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert17(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert13(::google::protobuf::uint32 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert7(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert4(::google::protobuf::uint64 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert1(double value)
{
    return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert2(float value)
{
   return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert9(const ::std::string &value)
{
    return PyUnicode_Decode(value.data(), value.length(), "utf-8", NULL);
}

static PyObject *
fastpb_convert12(const ::std::string &value)
{
    return PyString_FromStringAndSize(value.data(), value.length());
}

static PyObject *
fastpb_convert8(bool value)
{
    return PyBool_FromLong(value ? 1 : 0);
}

static PyObject *
fastpb_convert14(int value)
{
    // TODO(robbyw): Check EnumName_IsValid(value)
    return PyInt_FromLong(value);
}





// Lets try not to pollute the global namespace
namespace {

  // Forward-declaration for recursive structures
  extern PyTypeObject DeltaCoordsType;

  typedef struct {
      PyObject_HEAD

      imposm::cache::internal::DeltaCoords *protobuf;
  } DeltaCoords;

  void
  DeltaCoords_dealloc(DeltaCoords* self)
  {
      delete self->protobuf;
      self->ob_type->tp_free((PyObject*)self);
  }

  PyObject *
  DeltaCoords_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      DeltaCoords *self;

      self = (DeltaCoords *)type->tp_alloc(type, 0);

      self->protobuf = new imposm::cache::internal::DeltaCoords();

      return (PyObject *)self;
  }

  PyObject *
  DeltaCoords_DebugString(DeltaCoords* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      result = self->protobuf->Utf8DebugString();
      Py_END_ALLOW_THREADS
      return PyUnicode_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaCoords_SerializeToString(DeltaCoords* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaCoords_SerializeMany(void *nothing, PyObject *values)
  {
      std::string result;
      google::protobuf::io::ZeroCopyOutputStream* output =
          new google::protobuf::io::StringOutputStream(&result);
      google::protobuf::io::CodedOutputStream* outputStream =
          new google::protobuf::io::CodedOutputStream(output);

      PyObject *sequence = PySequence_Fast(values, "The values to serialize must be a sequence.");
      for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          DeltaCoords *value = (DeltaCoords *)PySequence_Fast_GET_ITEM(sequence, i);

          Py_BEGIN_ALLOW_THREADS
          outputStream->WriteVarint32(value->protobuf->ByteSize());
          value->protobuf->SerializeToCodedStream(outputStream);
          Py_END_ALLOW_THREADS
      }

      Py_XDECREF(sequence);
      delete outputStream;
      delete output;
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaCoords_ParseFromString(DeltaCoords* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  PyObject *
  DeltaCoords_ParseFromLongString(DeltaCoords* self, PyObject *value)
  {
      google::protobuf::io::ZeroCopyInputStream* input =
          new google::protobuf::io::ArrayInputStream(PyString_AsString(value), PyString_Size(value));
      google::protobuf::io::CodedInputStream* inputStream =
          new google::protobuf::io::CodedInputStream(input);
      inputStream->SetTotalBytesLimit(512 * 1024 * 1024, 512 * 1024 * 1024);

      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromCodedStream(inputStream);
      Py_END_ALLOW_THREADS

      delete inputStream;
      delete input;

      Py_RETURN_NONE;
  }


  PyObject *
  DeltaCoords_ParseMany(void* nothing, PyObject *args)
  {
      PyObject *value;
      PyObject *callback;
      int fail = 0;

      if (!PyArg_ParseTuple(args, "OO", &value, &callback)) {
          return NULL;
      }

      google::protobuf::io::ZeroCopyInputStream* input =
          new google::protobuf::io::ArrayInputStream(PyString_AsString(value), PyString_Size(value));
      google::protobuf::io::CodedInputStream* inputStream =
          new google::protobuf::io::CodedInputStream(input);
      inputStream->SetTotalBytesLimit(512 * 1024 * 1024, 512 * 1024 * 1024);

      google::protobuf::uint32 bytes;
      PyObject *single = NULL;
      while (inputStream->ReadVarint32(&bytes)) {
          google::protobuf::io::CodedInputStream::Limit messageLimit = inputStream->PushLimit(bytes);

          if (single == NULL) {
            single = DeltaCoords_new(&DeltaCoordsType, NULL, NULL);
          }

          Py_BEGIN_ALLOW_THREADS
          ((DeltaCoords *)single)->protobuf->ParseFromCodedStream(inputStream);
          Py_END_ALLOW_THREADS

          inputStream->PopLimit(messageLimit);
          PyObject *result = PyObject_CallFunctionObjArgs(callback, single, NULL);
          if (result == NULL) {
              fail = 1;
              break;
          };

          if (single->ob_refcnt != 1) {
            // If the callback saved a reference to the item, don't re-use it.
            Py_XDECREF(single);
            single = NULL;
          }
      }
      if (single != NULL) {
        Py_XDECREF(single);
      }

      delete inputStream;
      delete input;

      if (fail) {
          return NULL;
      } else {
          Py_RETURN_NONE;
      }
  }


  
    

    PyObject *
    DeltaCoords_getids(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->ids_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->ids(i));
            if (!value) {
              return NULL;
            }
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    int
    DeltaCoords_setids(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_ids();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The ids attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The ids attribute value must be a sequence");
        self->protobuf->clear_ids();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int64 protoValue;

        // int64
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsLongLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The ids attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_ids(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    PyObject *
    DeltaCoords_getlats(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->lats_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->lats(i));
            if (!value) {
              return NULL;
            }
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    int
    DeltaCoords_setlats(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lats();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lats attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lats attribute value must be a sequence");
        self->protobuf->clear_lats();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int64 protoValue;

        // int64
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsLongLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The lats attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_lats(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    PyObject *
    DeltaCoords_getlons(DeltaCoords *self, void *closure)
    {
        
          int len = self->protobuf->lons_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->lons(i));
            if (!value) {
              return NULL;
            }
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    int
    DeltaCoords_setlons(DeltaCoords *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_lons();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The lons attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The lons attribute value must be a sequence");
        self->protobuf->clear_lons();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int64 protoValue;

        // int64
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsLongLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The lons attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_lons(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  int
  DeltaCoords_init(DeltaCoords *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *ids = NULL;
        
          PyObject *lats = NULL;
        
          PyObject *lons = NULL;
        

        static char *kwlist[] = {
          
            (char *) "ids",
          
            (char *) "lats",
          
            (char *) "lons",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &ids,&lats,&lons))
          return -1;

        
          if (ids) {
            if (DeltaCoords_setids(self, ids, NULL) < 0) {
              return -1;
            }
          }
        
          if (lats) {
            if (DeltaCoords_setlats(self, lats, NULL) < 0) {
              return -1;
            }
          }
        
          if (lons) {
            if (DeltaCoords_setlons(self, lons, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }


  PyObject *
  DeltaCoords_richcompare(PyObject *self, PyObject *other, int op)
  {
      PyObject *result = NULL;
      if (!PyType_IsSubtype(other->ob_type, &DeltaCoordsType)) {
          result = Py_NotImplemented;
      } else {
          // This is not a particularly efficient implementation since it never short circuits, but it's better
          // than nothing.  It should probably only be used for tests.
          DeltaCoords *selfValue = (DeltaCoords *)self;
          DeltaCoords *otherValue = (DeltaCoords *)other;
          std::string selfSerialized;
          std::string otherSerialized;
          Py_BEGIN_ALLOW_THREADS
          selfValue->protobuf->SerializeToString(&selfSerialized);
          otherValue->protobuf->SerializeToString(&otherSerialized);
          Py_END_ALLOW_THREADS

          int cmp = selfSerialized.compare(otherSerialized);
          bool value = false;
          switch (op) {
              case Py_LT:
                  value = cmp < 0;
                  break;
              case Py_LE:
                  value = cmp <= 0;
                  break;
              case Py_EQ:
                  value = cmp == 0;
                  break;
              case Py_NE:
                  value = cmp != 0;
                  break;
              case Py_GT:
                  value = cmp > 0;
                  break;
              case Py_GE:
                  value = cmp >= 0;
                  break;
          }
          result = value ? Py_True : Py_False;
      }

      Py_XINCREF(result);
      return result;
  }


  static PyObject *
  DeltaCoords_repr(PyObject *selfObject)
  {
      DeltaCoords *self = (DeltaCoords *)selfObject;
      PyObject *member;
      PyObject *memberRepr;
      std::stringstream result;
      result << "DeltaCoords(";

      
        
        result << "ids=";
        member = DeltaCoords_getids(self, NULL);
        memberRepr = PyObject_Repr(member);
        result << PyString_AsString(memberRepr);
        Py_XDECREF(memberRepr);
        Py_XDECREF(member);
      
        
          result << ", ";
        
        result << "lats=";
        member = DeltaCoords_getlats(self, NULL);
        memberRepr = PyObject_Repr(member);
        result << PyString_AsString(memberRepr);
        Py_XDECREF(memberRepr);
        Py_XDECREF(member);
      
        
          result << ", ";
        
        result << "lons=";
        member = DeltaCoords_getlons(self, NULL);
        memberRepr = PyObject_Repr(member);
        result << PyString_AsString(memberRepr);
        Py_XDECREF(memberRepr);
        Py_XDECREF(member);
      

      result << ")";

      std::string resultString = result.str();
      return PyUnicode_Decode(resultString.data(), resultString.length(), "utf-8", NULL);
  }


  PyMemberDef DeltaCoords_members[] = {
      {NULL}  // Sentinel
  };


  PyGetSetDef DeltaCoords_getsetters[] = {
    
      {(char *)"ids",
       (getter)DeltaCoords_getids, (setter)DeltaCoords_setids,
       (char *)"",
       NULL},
    
      {(char *)"lats",
       (getter)DeltaCoords_getlats, (setter)DeltaCoords_setlats,
       (char *)"",
       NULL},
    
      {(char *)"lons",
       (getter)DeltaCoords_getlons, (setter)DeltaCoords_setlons,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  PyMethodDef DeltaCoords_methods[] = {
      {"DebugString", (PyCFunction)DeltaCoords_DebugString, METH_NOARGS,
       "Generates a human readable form of this message, useful for debugging and other purposes."
      },
      {"SerializeToString", (PyCFunction)DeltaCoords_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"SerializeMany", (PyCFunction)DeltaCoords_SerializeMany, METH_O | METH_CLASS,
       "Serializes a sequence of protocol buffers to a string."
      },
      {"ParseFromString", (PyCFunction)DeltaCoords_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {"ParseFromLongString", (PyCFunction)DeltaCoords_ParseFromLongString, METH_O,
       "Parses the protocol buffer from a string as large as 512MB."
      },
      {"ParseMany", (PyCFunction)DeltaCoords_ParseMany, METH_VARARGS | METH_CLASS,
       "Parses many protocol buffers of this type from a string."
      },
      {NULL}  // Sentinel
  };


  PyTypeObject DeltaCoordsType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "imposm.cache.internal.DeltaCoords",  /*tp_name*/
      sizeof(DeltaCoords),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)DeltaCoords_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      DeltaCoords_repr,                /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_RICHCOMPARE, /*tp_flags*/
      "DeltaCoords objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      DeltaCoords_richcompare,         /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      DeltaCoords_methods,             /* tp_methods */
      DeltaCoords_members,             /* tp_members */
      DeltaCoords_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)DeltaCoords_init,      /* tp_init */
      0,                                      /* tp_alloc */
      DeltaCoords_new,                 /* tp_new */
  };
}



// Lets try not to pollute the global namespace
namespace {

  // Forward-declaration for recursive structures
  extern PyTypeObject DeltaListType;

  typedef struct {
      PyObject_HEAD

      imposm::cache::internal::DeltaList *protobuf;
  } DeltaList;

  void
  DeltaList_dealloc(DeltaList* self)
  {
      delete self->protobuf;
      self->ob_type->tp_free((PyObject*)self);
  }

  PyObject *
  DeltaList_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      DeltaList *self;

      self = (DeltaList *)type->tp_alloc(type, 0);

      self->protobuf = new imposm::cache::internal::DeltaList();

      return (PyObject *)self;
  }

  PyObject *
  DeltaList_DebugString(DeltaList* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      result = self->protobuf->Utf8DebugString();
      Py_END_ALLOW_THREADS
      return PyUnicode_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaList_SerializeToString(DeltaList* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaList_SerializeMany(void *nothing, PyObject *values)
  {
      std::string result;
      google::protobuf::io::ZeroCopyOutputStream* output =
          new google::protobuf::io::StringOutputStream(&result);
      google::protobuf::io::CodedOutputStream* outputStream =
          new google::protobuf::io::CodedOutputStream(output);

      PyObject *sequence = PySequence_Fast(values, "The values to serialize must be a sequence.");
      for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          DeltaList *value = (DeltaList *)PySequence_Fast_GET_ITEM(sequence, i);

          Py_BEGIN_ALLOW_THREADS
          outputStream->WriteVarint32(value->protobuf->ByteSize());
          value->protobuf->SerializeToCodedStream(outputStream);
          Py_END_ALLOW_THREADS
      }

      Py_XDECREF(sequence);
      delete outputStream;
      delete output;
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  PyObject *
  DeltaList_ParseFromString(DeltaList* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  PyObject *
  DeltaList_ParseFromLongString(DeltaList* self, PyObject *value)
  {
      google::protobuf::io::ZeroCopyInputStream* input =
          new google::protobuf::io::ArrayInputStream(PyString_AsString(value), PyString_Size(value));
      google::protobuf::io::CodedInputStream* inputStream =
          new google::protobuf::io::CodedInputStream(input);
      inputStream->SetTotalBytesLimit(512 * 1024 * 1024, 512 * 1024 * 1024);

      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromCodedStream(inputStream);
      Py_END_ALLOW_THREADS

      delete inputStream;
      delete input;

      Py_RETURN_NONE;
  }


  PyObject *
  DeltaList_ParseMany(void* nothing, PyObject *args)
  {
      PyObject *value;
      PyObject *callback;
      int fail = 0;

      if (!PyArg_ParseTuple(args, "OO", &value, &callback)) {
          return NULL;
      }

      google::protobuf::io::ZeroCopyInputStream* input =
          new google::protobuf::io::ArrayInputStream(PyString_AsString(value), PyString_Size(value));
      google::protobuf::io::CodedInputStream* inputStream =
          new google::protobuf::io::CodedInputStream(input);
      inputStream->SetTotalBytesLimit(512 * 1024 * 1024, 512 * 1024 * 1024);

      google::protobuf::uint32 bytes;
      PyObject *single = NULL;
      while (inputStream->ReadVarint32(&bytes)) {
          google::protobuf::io::CodedInputStream::Limit messageLimit = inputStream->PushLimit(bytes);

          if (single == NULL) {
            single = DeltaList_new(&DeltaListType, NULL, NULL);
          }

          Py_BEGIN_ALLOW_THREADS
          ((DeltaList *)single)->protobuf->ParseFromCodedStream(inputStream);
          Py_END_ALLOW_THREADS

          inputStream->PopLimit(messageLimit);
          PyObject *result = PyObject_CallFunctionObjArgs(callback, single, NULL);
          if (result == NULL) {
              fail = 1;
              break;
          };

          if (single->ob_refcnt != 1) {
            // If the callback saved a reference to the item, don't re-use it.
            Py_XDECREF(single);
            single = NULL;
          }
      }
      if (single != NULL) {
        Py_XDECREF(single);
      }

      delete inputStream;
      delete input;

      if (fail) {
          return NULL;
      } else {
          Py_RETURN_NONE;
      }
  }


  
    

    PyObject *
    DeltaList_getids(DeltaList *self, void *closure)
    {
        
          int len = self->protobuf->ids_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert18(
                    self->protobuf->ids(i));
            if (!value) {
              return NULL;
            }
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    int
    DeltaList_setids(DeltaList *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_ids();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The ids attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The ids attribute value must be a sequence");
        self->protobuf->clear_ids();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        ::google::protobuf::int64 protoValue;

        // int64
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsLong(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsLongLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The ids attribute value must be an integer");
          return -1;
        }

      

      
          
            self->protobuf->add_ids(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  int
  DeltaList_init(DeltaList *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *ids = NULL;
        

        static char *kwlist[] = {
          
            (char *) "ids",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &ids))
          return -1;

        
          if (ids) {
            if (DeltaList_setids(self, ids, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }


  PyObject *
  DeltaList_richcompare(PyObject *self, PyObject *other, int op)
  {
      PyObject *result = NULL;
      if (!PyType_IsSubtype(other->ob_type, &DeltaListType)) {
          result = Py_NotImplemented;
      } else {
          // This is not a particularly efficient implementation since it never short circuits, but it's better
          // than nothing.  It should probably only be used for tests.
          DeltaList *selfValue = (DeltaList *)self;
          DeltaList *otherValue = (DeltaList *)other;
          std::string selfSerialized;
          std::string otherSerialized;
          Py_BEGIN_ALLOW_THREADS
          selfValue->protobuf->SerializeToString(&selfSerialized);
          otherValue->protobuf->SerializeToString(&otherSerialized);
          Py_END_ALLOW_THREADS

          int cmp = selfSerialized.compare(otherSerialized);
          bool value = false;
          switch (op) {
              case Py_LT:
                  value = cmp < 0;
                  break;
              case Py_LE:
                  value = cmp <= 0;
                  break;
              case Py_EQ:
                  value = cmp == 0;
                  break;
              case Py_NE:
                  value = cmp != 0;
                  break;
              case Py_GT:
                  value = cmp > 0;
                  break;
              case Py_GE:
                  value = cmp >= 0;
                  break;
          }
          result = value ? Py_True : Py_False;
      }

      Py_XINCREF(result);
      return result;
  }


  static PyObject *
  DeltaList_repr(PyObject *selfObject)
  {
      DeltaList *self = (DeltaList *)selfObject;
      PyObject *member;
      PyObject *memberRepr;
      std::stringstream result;
      result << "DeltaList(";

      
        
        result << "ids=";
        member = DeltaList_getids(self, NULL);
        memberRepr = PyObject_Repr(member);
        result << PyString_AsString(memberRepr);
        Py_XDECREF(memberRepr);
        Py_XDECREF(member);
      

      result << ")";

      std::string resultString = result.str();
      return PyUnicode_Decode(resultString.data(), resultString.length(), "utf-8", NULL);
  }


  PyMemberDef DeltaList_members[] = {
      {NULL}  // Sentinel
  };


  PyGetSetDef DeltaList_getsetters[] = {
    
      {(char *)"ids",
       (getter)DeltaList_getids, (setter)DeltaList_setids,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  PyMethodDef DeltaList_methods[] = {
      {"DebugString", (PyCFunction)DeltaList_DebugString, METH_NOARGS,
       "Generates a human readable form of this message, useful for debugging and other purposes."
      },
      {"SerializeToString", (PyCFunction)DeltaList_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"SerializeMany", (PyCFunction)DeltaList_SerializeMany, METH_O | METH_CLASS,
       "Serializes a sequence of protocol buffers to a string."
      },
      {"ParseFromString", (PyCFunction)DeltaList_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {"ParseFromLongString", (PyCFunction)DeltaList_ParseFromLongString, METH_O,
       "Parses the protocol buffer from a string as large as 512MB."
      },
      {"ParseMany", (PyCFunction)DeltaList_ParseMany, METH_VARARGS | METH_CLASS,
       "Parses many protocol buffers of this type from a string."
      },
      {NULL}  // Sentinel
  };


  PyTypeObject DeltaListType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "imposm.cache.internal.DeltaList",  /*tp_name*/
      sizeof(DeltaList),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)DeltaList_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      DeltaList_repr,                /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_RICHCOMPARE, /*tp_flags*/
      "DeltaList objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      DeltaList_richcompare,         /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      DeltaList_methods,             /* tp_methods */
      DeltaList_members,             /* tp_members */
      DeltaList_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)DeltaList_init,      /* tp_init */
      0,                                      /* tp_alloc */
      DeltaList_new,                 /* tp_new */
  };
}



static PyMethodDef module_methods[] = {
    {NULL}  // Sentinel
};

#ifndef PyMODINIT_FUNC	// Declarations for DLL import/export.
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initinternal(void)
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    PyObject* m;

    

    
      if (PyType_Ready(&DeltaCoordsType) < 0)
          return;
    
      if (PyType_Ready(&DeltaListType) < 0)
          return;
    

    m = Py_InitModule3("internal", module_methods,
                       "");

    if (m == NULL)
      return;

    

    
      Py_INCREF(&DeltaCoordsType);
      PyModule_AddObject(m, "DeltaCoords", (PyObject *)&DeltaCoordsType);
    
      Py_INCREF(&DeltaListType);
      PyModule_AddObject(m, "DeltaList", (PyObject *)&DeltaListType);
    
}